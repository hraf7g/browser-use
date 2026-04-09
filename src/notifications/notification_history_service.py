from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models.email_delivery import EmailDelivery
from src.shared.schemas.notification_history import (
    NotificationDeliveryHistoryItem,
    NotificationDeliveryHistoryResponse,
)


def list_notification_delivery_history(
    session: Session,
    *,
    user_id,
    page: int,
    limit: int,
) -> NotificationDeliveryHistoryResponse:
    """
    Return the user's paginated email-delivery history in deterministic order.

    Notes:
        - This function does not commit the transaction.
        - Newest deliveries are returned first by attempted_at desc, then id desc.
    """
    offset = (page - 1) * limit

    total = session.execute(
        select(func.count())
        .select_from(EmailDelivery)
        .where(EmailDelivery.user_id == user_id)
    ).scalar_one()

    rows = session.execute(
        select(EmailDelivery)
        .where(EmailDelivery.user_id == user_id)
        .order_by(EmailDelivery.attempted_at.desc(), EmailDelivery.id.desc())
        .offset(offset)
        .limit(limit)
    ).scalars().all()

    return NotificationDeliveryHistoryResponse(
        page=page,
        limit=limit,
        total=total,
        items=[
            NotificationDeliveryHistoryItem(
                id=row.id,
                delivery_type=row.delivery_type,
                status=row.status,
                attempted_at=row.attempted_at,
                sent_at=row.sent_at,
                match_count=row.match_count,
                failure_reason=row.failure_reason,
            )
            for row in rows
        ],
    )
