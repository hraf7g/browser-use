from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from sqlalchemy import select

from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR
from src.jobs.job_lock_service import acquire_named_job_lock, release_named_job_lock
from src.notifications.instant_alert_service import (
    dispatch_pending_instant_alerts_for_user,
)
from src.notifications.notification_preference_service import (
    get_or_create_notification_preference,
)

SEND_PENDING_INSTANT_ALERTS_JOB_LOCK_NAME: Final[str] = (
    "utw:send_pending_instant_alerts_job"
)


class SendPendingInstantAlertsJobAlreadyRunningError(RuntimeError):
    """Raised when another session already holds the instant-alert job lock."""


@dataclass(frozen=True)
class SendPendingInstantAlertsJobResult:
    """Compact result for one instant-alert batch dispatch job."""

    processed_user_count: int
    sent_delivery_count: int
    skipped_user_count: int
    overall_status: str


def run_send_pending_instant_alerts_job(
    *,
    outbox_dir: Path | str = DEFAULT_DEV_OUTBOX_DIR,
) -> SendPendingInstantAlertsJobResult:
    """
    Execute one persisted pending-instant-alert dispatch job.

    Notes:
        - Opens its own database session.
        - Acquires a DB advisory lock before dispatching.
        - Commits on success.
        - Rolls back and re-raises unexpected exceptions.
        - Dispatches users sequentially in deterministic user-id order.
    """
    session_factory = get_session_factory()

    with session_factory() as session:
        lock_acquired = False
        try:
            lock_acquired = acquire_named_job_lock(
                session,
                job_name=SEND_PENDING_INSTANT_ALERTS_JOB_LOCK_NAME,
            )
            if not lock_acquired:
                raise SendPendingInstantAlertsJobAlreadyRunningError(
                    "pending instant-alert job is already running in another session"
                )

            pending_user_ids = _list_pending_instant_alert_user_ids(session)
            processed_user_count = 0
            sent_delivery_count = 0
            skipped_user_count = 0

            for user_id in pending_user_ids:
                processed_user_count += 1
                preference = get_or_create_notification_preference(
                    session,
                    user_id=user_id,
                )
                if not preference.email_enabled or not preference.instant_alert_enabled:
                    skipped_user_count += 1
                    continue

                dispatch_result = dispatch_pending_instant_alerts_for_user(
                    session=session,
                    user_id=user_id,
                    outbox_dir=outbox_dir,
                )
                if dispatch_result is None:
                    skipped_user_count += 1
                    continue

                sent_delivery_count += 1

            session.commit()
            return SendPendingInstantAlertsJobResult(
                processed_user_count=processed_user_count,
                sent_delivery_count=sent_delivery_count,
                skipped_user_count=skipped_user_count,
                overall_status="success",
            )
        except Exception:
            session.rollback()
            raise
        finally:
            if lock_acquired:
                released = release_named_job_lock(
                    session,
                    job_name=SEND_PENDING_INSTANT_ALERTS_JOB_LOCK_NAME,
                )
                if not released:
                    raise RuntimeError(
                        "expected pending instant-alert job lock release to succeed"
                    )


def _list_pending_instant_alert_user_ids(session) -> list:
    """Return distinct user ids with pending instant-alert matches in stable order."""
    return list(
        session.execute(
            select(TenderMatch.user_id)
            .where(
                TenderMatch.sent_at.is_(None),
                TenderMatch.alerted_at.is_(None),
            )
            .distinct()
            .order_by(TenderMatch.user_id.asc())
        )
        .scalars()
        .all()
    )
