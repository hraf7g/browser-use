from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from sqlalchemy import select

from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR
from src.email.email_delivery_outbox_service import (
    deliver_pending_email_delivery,
    list_pending_email_delivery_ids,
    mark_email_delivery_failed,
    mark_email_delivery_sent,
    queue_instant_alert_delivery_for_user,
)
from src.jobs.job_lock_service import acquire_named_job_lock, finalize_named_job_lock
from src.notifications.notification_preference_service import (
    get_or_create_notification_preference,
)
from src.shared.logging.logger import get_logger

SEND_PENDING_INSTANT_ALERTS_JOB_LOCK_NAME: Final[str] = (
    "utw:send_pending_instant_alerts_job"
)
logger = get_logger(__name__)


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

    with session_factory() as lock_session:
        lock_acquired = False
        active_error: Exception | None = None
        try:
            lock_acquired = acquire_named_job_lock(
                lock_session,
                job_name=SEND_PENDING_INSTANT_ALERTS_JOB_LOCK_NAME,
            )
            if not lock_acquired:
                raise SendPendingInstantAlertsJobAlreadyRunningError(
                    "pending instant-alert job is already running in another session"
                )

            with session_factory() as read_session:
                pending_user_ids = _list_pending_instant_alert_user_ids(read_session)
            processed_user_count = 0
            sent_delivery_count = 0
            skipped_user_count = 0

            for user_id in pending_user_ids:
                processed_user_count += 1
                with session_factory() as queue_session:
                    preference = get_or_create_notification_preference(
                        queue_session,
                        user_id=user_id,
                    )
                    if (
                        not preference.email_enabled
                        or not preference.instant_alert_enabled
                    ):
                        skipped_user_count += 1
                        queue_session.rollback()
                        continue

                    queued_result = queue_instant_alert_delivery_for_user(
                        queue_session,
                        user_id=user_id,
                    )
                    if queued_result is None:
                        skipped_user_count += 1
                        queue_session.rollback()
                        continue

                    queue_session.commit()

            with session_factory() as pending_session:
                pending_delivery_ids = list_pending_email_delivery_ids(
                    pending_session,
                    delivery_type="instant_alert",
                )

            for email_delivery_id in pending_delivery_ids:
                with session_factory() as delivery_session:
                    try:
                        backend_result = deliver_pending_email_delivery(
                            delivery_session,
                            email_delivery_id=email_delivery_id,
                            outbox_dir=outbox_dir,
                        )
                    except Exception as exc:
                        delivery_session.rollback()
                        _mark_delivery_failed(
                            session_factory=session_factory,
                            email_delivery_id=email_delivery_id,
                            failure_reason=str(exc),
                        )
                        raise

                with session_factory() as finalize_session:
                    mark_email_delivery_sent(
                        finalize_session,
                        email_delivery_id=email_delivery_id,
                        backend_result=backend_result,
                    )
                    finalize_session.commit()
                sent_delivery_count += 1

            return SendPendingInstantAlertsJobResult(
                processed_user_count=processed_user_count,
                sent_delivery_count=sent_delivery_count,
                skipped_user_count=skipped_user_count,
                overall_status="success",
            )
        except Exception as exc:
            active_error = exc
            raise
        finally:
            if lock_acquired:
                finalize_named_job_lock(
                    lock_session,
                    job_name=SEND_PENDING_INSTANT_ALERTS_JOB_LOCK_NAME,
                    logger=logger,
                    active_error=active_error,
                )


def _mark_delivery_failed(
    *,
    session_factory,
    email_delivery_id,
    failure_reason: str,
) -> None:
    """Persist a failed instant-alert delivery finalization."""
    with session_factory() as failure_session:
        mark_email_delivery_failed(
            failure_session,
            email_delivery_id=email_delivery_id,
            failure_reason=failure_reason,
        )
        failure_session.commit()


def _list_pending_instant_alert_user_ids(session) -> list:
    """Return distinct user ids with unqueued pending instant-alert matches in stable order."""
    return list(
        session.execute(
            select(TenderMatch.user_id)
            .where(
                TenderMatch.sent_at.is_(None),
                TenderMatch.alerted_at.is_(None),
                TenderMatch.instant_alert_queued_at.is_(None),
            )
            .distinct()
            .order_by(TenderMatch.user_id.asc())
        )
        .scalars()
        .all()
    )
