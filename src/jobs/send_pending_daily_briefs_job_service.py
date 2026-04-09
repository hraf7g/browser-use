from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from sqlalchemy import select

from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.email.daily_brief_dispatch_service import dispatch_daily_brief_for_user
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR
from src.jobs.job_lock_service import acquire_named_job_lock, release_named_job_lock
from src.notifications.notification_preference_service import (
    get_or_create_notification_preference,
)

SEND_PENDING_DAILY_BRIEFS_JOB_LOCK_NAME: Final[str] = (
    "utw:send_pending_daily_briefs_job"
)


class SendPendingDailyBriefsJobAlreadyRunningError(RuntimeError):
    """Raised when another session already holds the daily-brief job lock."""


@dataclass(frozen=True)
class SendPendingDailyBriefsJobResult:
    """Compact result for one daily-brief batch dispatch job."""

    processed_user_count: int
    sent_delivery_count: int
    skipped_user_count: int
    overall_status: str


def run_send_pending_daily_briefs_job(
    *,
    outbox_dir: Path | str = DEFAULT_DEV_OUTBOX_DIR,
) -> SendPendingDailyBriefsJobResult:
    """
    Execute one persisted pending-daily-brief dispatch job.

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
                job_name=SEND_PENDING_DAILY_BRIEFS_JOB_LOCK_NAME,
            )
            if not lock_acquired:
                raise SendPendingDailyBriefsJobAlreadyRunningError(
                    "pending daily-brief job is already running in another session"
                )

            pending_user_ids = _list_pending_daily_brief_user_ids(session)
            processed_user_count = 0
            sent_delivery_count = 0
            skipped_user_count = 0

            for user_id in pending_user_ids:
                processed_user_count += 1
                preference = get_or_create_notification_preference(
                    session,
                    user_id=user_id,
                )
                if not preference.email_enabled or not preference.daily_brief_enabled:
                    skipped_user_count += 1
                    continue

                dispatch_result = dispatch_daily_brief_for_user(
                    session=session,
                    user_id=user_id,
                    outbox_dir=outbox_dir,
                )
                if dispatch_result is None:
                    skipped_user_count += 1
                    continue

                sent_delivery_count += 1

            session.commit()
            return SendPendingDailyBriefsJobResult(
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
                    job_name=SEND_PENDING_DAILY_BRIEFS_JOB_LOCK_NAME,
                )
                if not released:
                    raise RuntimeError(
                        "expected pending daily-brief job lock release to succeed"
                    )


def _list_pending_daily_brief_user_ids(session) -> list:
    """Return distinct user ids with unsent tender matches in stable order."""
    return list(
        session.execute(
            select(TenderMatch.user_id)
            .where(TenderMatch.sent_at.is_(None))
            .distinct()
            .order_by(TenderMatch.user_id.asc())
        )
        .scalars()
        .all()
    )
