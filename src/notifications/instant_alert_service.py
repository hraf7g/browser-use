from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.email_delivery import EmailDelivery
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.db.models.user import User
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR, send_dev_email
from src.notifications.notification_preference_service import (
    get_or_create_notification_preference,
)
from src.shared.schemas.email import EmailMessage


class InstantAlertError(ValueError):
    """Base class for instant-alert service failures."""


class InstantAlertUserNotFoundError(InstantAlertError):
    """Raised when the target user does not exist."""


class InstantAlertInactiveUserError(InstantAlertError):
    """Raised when the target user is inactive."""


@dataclass(frozen=True)
class InstantAlertDispatchResult:
    """Result metadata for one dispatched instant-alert email."""

    user_id: UUID
    match_ids: list[UUID]
    tender_ids: list[UUID]
    email_delivery_id: UUID
    backend_message_id: str
    output_path: Path


def dispatch_pending_instant_alerts_for_user(
    session: Session,
    *,
    user_id: UUID,
    outbox_dir: Path | str = DEFAULT_DEV_OUTBOX_DIR,
) -> InstantAlertDispatchResult | None:
    """
    Dispatch one user's pending instant alerts by email.

    Returns:
        InstantAlertDispatchResult | None:
            - None when preferences disable instant alerts or there are no pending rows
            - otherwise dispatch metadata for the created delivery

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
        - Instant alerts only consider rows not yet included in a brief and not yet alerted.
        - This function records one EmailDelivery row with delivery_type='instant_alert'.
        - This function marks included tender matches via TenderMatch.alerted_at.
    """
    user = session.get(User, user_id)
    if user is None:
        raise InstantAlertUserNotFoundError(f"user '{user_id}' was not found")

    if not user.is_active:
        raise InstantAlertInactiveUserError(f"user '{user_id}' is inactive")

    preference = get_or_create_notification_preference(
        session,
        user_id=user_id,
    )
    if not preference.email_enabled or not preference.instant_alert_enabled:
        return None

    rows = session.execute(
        select(TenderMatch, Tender, Source)
        .join(Tender, Tender.id == TenderMatch.tender_id)
        .join(Source, Source.id == Tender.source_id)
        .where(
            TenderMatch.user_id == user_id,
            TenderMatch.sent_at.is_(None),
            TenderMatch.alerted_at.is_(None),
        )
        .order_by(
            Tender.closing_date.asc(),
            Tender.created_at.desc(),
            Tender.id.asc(),
        )
    ).all()

    if not rows:
        return None

    match_ids: list[UUID] = []
    tender_ids: list[UUID] = []
    rendered_items: list[str] = []

    for index, row in enumerate(rows, start=1):
        tender_match, tender, source = row
        match_ids.append(tender_match.id)
        tender_ids.append(tender.id)
        rendered_items.append(
            _render_tender_match_block(
                position=index,
                tender=tender,
                source=source,
                tender_match=tender_match,
            )
        )

    email_message = EmailMessage(
        to=user.email,
        subject=_build_subject(match_count=len(match_ids)),
        body_text=_build_body(rendered_items),
    )
    delivery_backend_result = send_dev_email(
        email_message,
        outbox_dir=outbox_dir,
    )

    alerted_at = datetime.now(timezone.utc)

    email_delivery = EmailDelivery(
        user_id=user.id,
        delivery_type="instant_alert",
        status="sent",
        attempted_at=alerted_at,
        sent_at=alerted_at,
        match_count=len(match_ids),
        failure_reason=None,
    )
    session.add(email_delivery)
    session.flush()

    matched_rows = session.execute(
        select(TenderMatch).where(TenderMatch.id.in_(match_ids))
    ).scalars().all()
    if len(matched_rows) != len(match_ids):
        raise ValueError("not all TenderMatch rows referenced by the instant alert were found")

    for tender_match in matched_rows:
        tender_match.alerted_at = alerted_at

    session.flush()

    return InstantAlertDispatchResult(
        user_id=user.id,
        match_ids=list(match_ids),
        tender_ids=list(tender_ids),
        email_delivery_id=email_delivery.id,
        backend_message_id=delivery_backend_result.message_id,
        output_path=delivery_backend_result.output_path,
    )


def _build_subject(*, match_count: int) -> str:
    """Build a deterministic instant-alert subject line."""
    if match_count == 1:
        return "UAE Tender Watch — 1 instant tender alert"
    return f"UAE Tender Watch — {match_count} instant tender alerts"


def _build_body(rendered_items: list[str]) -> str:
    """Build the plain-text instant-alert email body."""
    lines = [
        "A new UAE Tender Watch instant alert is ready.",
        "",
        "New matching tenders:",
        "",
        *rendered_items,
        "Open the dashboard to review and act on these opportunities.",
    ]
    return "\n".join(lines).strip()


def _render_tender_match_block(
    *,
    position: int,
    tender: Tender,
    source: Source,
    tender_match: TenderMatch,
) -> str:
    """Render one matched tender entry for the instant alert."""
    matched_keywords = ", ".join(tender_match.matched_keywords or [])
    lines = [
        f"{position}. {tender.title}",
        f"   Entity: {tender.issuing_entity}",
        f"   Source: {source.name}",
        f"   Closing Date: {tender.closing_date.isoformat()}",
    ]

    if tender.tender_ref:
        lines.append(f"   Reference: {tender.tender_ref}")

    if tender.category:
        lines.append(f"   Category: {tender.category}")

    if matched_keywords:
        lines.append(f"   Matched Keywords: {matched_keywords}")

    if tender.ai_summary:
        lines.append(f"   Summary: {tender.ai_summary}")

    lines.append(f"   Source Link: {tender.source_url}")
    lines.append("")
    return "\n".join(lines)
