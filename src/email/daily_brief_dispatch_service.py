from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.email_delivery import EmailDelivery
from src.db.models.tender_match import TenderMatch
from src.email.backend import send_email_message
from src.email.daily_brief_service import (
    build_daily_brief_for_user,
)
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR


@dataclass(frozen=True)
class DailyBriefDispatchResult:
    """Result metadata for one dispatched daily brief."""

    user_id: UUID
    match_ids: list[UUID]
    tender_ids: list[UUID]
    email_delivery_id: UUID
    backend_message_id: str
    output_path: Path | None


def dispatch_daily_brief_for_user(
    session: Session,
    *,
    user_id: UUID,
    outbox_dir: Path | str = DEFAULT_DEV_OUTBOX_DIR,
) -> DailyBriefDispatchResult | None:
    """
    Build and dispatch one user's daily brief using the configured email backend.

    Returns:
        DailyBriefDispatchResult | None:
            - None when there are no unsent matches
            - otherwise dispatch metadata for the created delivery

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
        - This function marks included tender matches as sent.
        - This function records one EmailDelivery row for the dispatched brief.
    """
    brief = build_daily_brief_for_user(
        session=session,
        user_id=user_id,
    )
    if brief is None:
        return None

    delivery_backend_result = send_email_message(
        brief.email_message,
        outbox_dir=outbox_dir,
    )

    sent_at = delivery_backend_result.delivered_at

    email_delivery = EmailDelivery(
        user_id=brief.user_id,
        delivery_type="daily_brief",
        status="sent",
        attempted_at=sent_at,
        sent_at=sent_at,
        match_count=len(brief.match_ids),
        failure_reason=None,
    )
    session.add(email_delivery)
    session.flush()

    matched_rows = session.execute(
        select(TenderMatch).where(TenderMatch.id.in_(brief.match_ids))
    ).scalars().all()

    if len(matched_rows) != len(brief.match_ids):
        raise ValueError("not all TenderMatch rows referenced by the daily brief were found")

    for tender_match in matched_rows:
        tender_match.sent_at = sent_at

    session.flush()

    return DailyBriefDispatchResult(
        user_id=brief.user_id,
        match_ids=list(brief.match_ids),
        tender_ids=list(brief.tender_ids),
        email_delivery_id=email_delivery.id,
        backend_message_id=delivery_backend_result.message_id,
        output_path=delivery_backend_result.output_path,
    )
