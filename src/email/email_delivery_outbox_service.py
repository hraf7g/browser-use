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
from src.email.backend import EmailDeliveryBackendResult, send_email_message
from src.email.daily_brief_service import build_daily_brief_for_user
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR
from src.shared.schemas.email import EmailMessage


class EmailDeliveryOutboxError(ValueError):
    """Base class for email outbox service failures."""


class PendingEmailDeliveryNotFoundError(EmailDeliveryOutboxError):
    """Raised when a pending delivery cannot be found."""


@dataclass(frozen=True)
class QueuedEmailDeliveryResult:
    """Metadata for one queued but not yet dispatched email delivery."""

    email_delivery_id: UUID
    user_id: UUID
    match_ids: list[UUID]
    tender_ids: list[UUID]


@dataclass(frozen=True)
class PendingEmailDeliveryPayload:
    """Persisted payload loaded from the durable delivery outbox."""

    email_delivery_id: UUID
    delivery_type: str
    user_id: UUID | None
    message: EmailMessage
    match_ids: list[UUID]
    tender_ids: list[UUID]


@dataclass(frozen=True)
class EmailDeliveryDispatchResult:
    """Result metadata for one durably dispatched email delivery."""

    email_delivery_id: UUID
    user_id: UUID | None
    match_ids: list[UUID]
    tender_ids: list[UUID]
    backend_message_id: str
    output_path: Path | None


def queue_daily_brief_delivery_for_user(
    session: Session,
    *,
    user_id: UUID,
) -> QueuedEmailDeliveryResult | None:
    """Queue one user's daily brief durably without sending it yet."""
    brief = build_daily_brief_for_user(
        session=session,
        user_id=user_id,
    )
    if brief is None:
        return None

    matched_rows = session.execute(
        select(TenderMatch).where(TenderMatch.id.in_(brief.match_ids))
    ).scalars().all()
    if len(matched_rows) != len(brief.match_ids):
        raise ValueError("not all TenderMatch rows referenced by the daily brief were found")

    queued_at = datetime.now(timezone.utc)
    for tender_match in matched_rows:
        tender_match.daily_brief_queued_at = queued_at

    email_delivery = EmailDelivery(
        user_id=brief.user_id,
        delivery_type="daily_brief",
        status="pending",
        attempted_at=queued_at,
        sent_at=None,
        match_count=len(brief.match_ids),
        recipient_email=brief.email_message.to,
        subject=brief.email_message.subject,
        body_text=brief.email_message.body_text,
        match_ids=list(brief.match_ids),
        tender_ids=list(brief.tender_ids),
        backend_message_id=None,
        backend_output_path=None,
        failure_reason=None,
    )
    session.add(email_delivery)
    session.flush()

    return QueuedEmailDeliveryResult(
        email_delivery_id=email_delivery.id,
        user_id=brief.user_id,
        match_ids=list(brief.match_ids),
        tender_ids=list(brief.tender_ids),
    )


def queue_instant_alert_delivery_for_user(
    session: Session,
    *,
    user_id: UUID,
) -> QueuedEmailDeliveryResult | None:
    """Queue one user's instant alert durably without sending it yet."""
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        return None

    rows = session.execute(
        select(TenderMatch, Tender, Source)
        .join(Tender, Tender.id == TenderMatch.tender_id)
        .join(Source, Source.id == Tender.source_id)
        .where(
            TenderMatch.user_id == user_id,
            TenderMatch.sent_at.is_(None),
            TenderMatch.alerted_at.is_(None),
            TenderMatch.instant_alert_queued_at.is_(None),
        )
        .order_by(
            Tender.closing_date.asc().nulls_last(),
            Tender.created_at.desc(),
            Tender.id.asc(),
        )
    ).all()
    if not rows:
        return None

    match_ids: list[UUID] = []
    tender_ids: list[UUID] = []
    rendered_items: list[str] = []
    queued_at = datetime.now(timezone.utc)

    for index, row in enumerate(rows, start=1):
        tender_match, tender, source = row
        tender_match.instant_alert_queued_at = queued_at
        match_ids.append(tender_match.id)
        tender_ids.append(tender.id)
        rendered_items.append(
            _render_instant_alert_tender_match_block(
                position=index,
                tender=tender,
                source=source,
                tender_match=tender_match,
            )
        )

    email_message = EmailMessage(
        to=user.email,
        subject=_build_instant_alert_subject(match_count=len(match_ids)),
        body_text=_build_instant_alert_body(rendered_items),
    )

    email_delivery = EmailDelivery(
        user_id=user.id,
        delivery_type="instant_alert",
        status="pending",
        attempted_at=queued_at,
        sent_at=None,
        match_count=len(match_ids),
        recipient_email=email_message.to,
        subject=email_message.subject,
        body_text=email_message.body_text,
        match_ids=list(match_ids),
        tender_ids=list(tender_ids),
        backend_message_id=None,
        backend_output_path=None,
        failure_reason=None,
    )
    session.add(email_delivery)
    session.flush()

    return QueuedEmailDeliveryResult(
        email_delivery_id=email_delivery.id,
        user_id=user.id,
        match_ids=list(match_ids),
        tender_ids=list(tender_ids),
    )


def list_pending_email_delivery_ids(
    session: Session,
    *,
    delivery_type: str,
) -> list[UUID]:
    """Return pending delivery ids in stable queue order."""
    return list(
        session.execute(
            select(EmailDelivery.id)
            .where(
                EmailDelivery.delivery_type == delivery_type,
                EmailDelivery.status == "pending",
            )
            .order_by(EmailDelivery.attempted_at.asc(), EmailDelivery.id.asc())
        )
        .scalars()
        .all()
    )


def load_pending_email_delivery_payload(
    session: Session,
    *,
    email_delivery_id: UUID,
) -> PendingEmailDeliveryPayload:
    """Load one pending delivery payload from the durable outbox."""
    email_delivery = session.get(EmailDelivery, email_delivery_id)
    if email_delivery is None or email_delivery.status != "pending":
        raise PendingEmailDeliveryNotFoundError(
            f"pending email delivery '{email_delivery_id}' was not found"
        )

    if not email_delivery.recipient_email or not email_delivery.subject or not email_delivery.body_text:
        raise ValueError("pending email delivery payload is incomplete")

    return PendingEmailDeliveryPayload(
        email_delivery_id=email_delivery.id,
        delivery_type=email_delivery.delivery_type,
        user_id=email_delivery.user_id,
        message=EmailMessage(
            to=email_delivery.recipient_email,
            subject=email_delivery.subject,
            body_text=email_delivery.body_text,
        ),
        match_ids=list(email_delivery.match_ids or []),
        tender_ids=list(email_delivery.tender_ids or []),
    )


def deliver_pending_email_delivery(
    session: Session,
    *,
    email_delivery_id: UUID,
    outbox_dir: Path | str = DEFAULT_DEV_OUTBOX_DIR,
) -> EmailDeliveryBackendResult:
    """Send one persisted pending delivery using the configured email backend."""
    payload = load_pending_email_delivery_payload(
        session,
        email_delivery_id=email_delivery_id,
    )
    return send_email_message(
        payload.message,
        outbox_dir=outbox_dir,
    )


def mark_email_delivery_sent(
    session: Session,
    *,
    email_delivery_id: UUID,
    backend_result: EmailDeliveryBackendResult,
) -> EmailDeliveryDispatchResult:
    """Finalize one pending delivery as sent and mark the related matches."""
    email_delivery = session.get(EmailDelivery, email_delivery_id)
    if email_delivery is None:
        raise PendingEmailDeliveryNotFoundError(
            f"email delivery '{email_delivery_id}' was not found"
        )

    sent_at = backend_result.delivered_at
    email_delivery.status = "sent"
    email_delivery.sent_at = sent_at
    email_delivery.backend_message_id = backend_result.message_id
    email_delivery.backend_output_path = (
        str(backend_result.output_path) if backend_result.output_path is not None else None
    )
    email_delivery.failure_reason = None

    match_ids = list(email_delivery.match_ids or [])
    matched_rows = session.execute(
        select(TenderMatch).where(TenderMatch.id.in_(match_ids))
    ).scalars().all()
    if len(matched_rows) != len(match_ids):
        raise ValueError("not all TenderMatch rows referenced by the email delivery were found")

    for tender_match in matched_rows:
        if email_delivery.delivery_type == "daily_brief":
            tender_match.sent_at = sent_at
            tender_match.daily_brief_queued_at = None
        elif email_delivery.delivery_type == "instant_alert":
            tender_match.alerted_at = sent_at
            tender_match.instant_alert_queued_at = None
        else:
            raise ValueError(
                f"unsupported delivery_type for sent finalization: {email_delivery.delivery_type!r}"
            )

    session.flush()

    return EmailDeliveryDispatchResult(
        email_delivery_id=email_delivery.id,
        user_id=email_delivery.user_id,
        match_ids=match_ids,
        tender_ids=list(email_delivery.tender_ids or []),
        backend_message_id=backend_result.message_id,
        output_path=backend_result.output_path,
    )


def mark_email_delivery_failed(
    session: Session,
    *,
    email_delivery_id: UUID,
    failure_reason: str,
) -> None:
    """Finalize one pending delivery as failed and release queued matches."""
    email_delivery = session.get(EmailDelivery, email_delivery_id)
    if email_delivery is None:
        raise PendingEmailDeliveryNotFoundError(
            f"email delivery '{email_delivery_id}' was not found"
        )

    email_delivery.status = "failed"
    email_delivery.sent_at = None
    email_delivery.backend_message_id = None
    email_delivery.backend_output_path = None
    email_delivery.failure_reason = failure_reason.strip()[:2000]

    match_ids = list(email_delivery.match_ids or [])
    matched_rows = session.execute(
        select(TenderMatch).where(TenderMatch.id.in_(match_ids))
    ).scalars().all()

    for tender_match in matched_rows:
        if email_delivery.delivery_type == "daily_brief":
            tender_match.daily_brief_queued_at = None
        elif email_delivery.delivery_type == "instant_alert":
            tender_match.instant_alert_queued_at = None

    session.flush()


def _build_instant_alert_subject(*, match_count: int) -> str:
    """Build a deterministic instant-alert subject line."""
    if match_count == 1:
        return "UAE Tender Watch — 1 instant tender alert"
    return f"UAE Tender Watch — {match_count} instant tender alerts"


def _build_instant_alert_body(rendered_items: list[str]) -> str:
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


def _render_instant_alert_tender_match_block(
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
        (
            f"   Closing Date: {tender.closing_date.isoformat()}"
            if tender.closing_date is not None
            else "   Closing Date: Unknown"
        ),
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
