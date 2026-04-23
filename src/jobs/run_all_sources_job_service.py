from __future__ import annotations

from src.db.session import get_session_factory
from src.jobs.job_lock_service import acquire_named_job_lock, finalize_named_job_lock
from src.operator.all_sources_run_service import (
    run_all_supported_sources_with_isolated_transactions,
)
from src.shared.logging.logger import get_logger
from src.shared.schemas.operator_run_batch import OperatorRunAllSourcesResponse

ALL_SOURCES_JOB_LOCK_NAME = "utw:run_all_sources_job"
logger = get_logger(__name__)


class AllSourcesJobAlreadyRunningError(RuntimeError):
    """Raised when another session already holds the all-sources job lock."""


def run_all_sources_job() -> OperatorRunAllSourcesResponse:
    """
    Execute one persisted all-sources batch run.

    Notes:
        - Opens its own database session.
        - Commits the batch if orchestration completes normally.
        - Rolls back and re-raises unexpected exceptions.
        - Scheduler integration is intentionally out of scope here.
    """
    session_factory = get_session_factory()

    with session_factory() as session:
        lock_acquired = False
        active_error: Exception | None = None
        try:
            lock_acquired = acquire_named_job_lock(
                session,
                job_name=ALL_SOURCES_JOB_LOCK_NAME,
            )
            if not lock_acquired:
                raise AllSourcesJobAlreadyRunningError(
                    "all-sources job is already running in another session"
                )

            result = run_all_supported_sources_with_isolated_transactions(
                session_factory=session_factory,
            )
            return result
        except Exception as exc:
            active_error = exc
            session.rollback()
            raise
        finally:
            if lock_acquired:
                finalize_named_job_lock(
                    session,
                    job_name=ALL_SOURCES_JOB_LOCK_NAME,
                    logger=logger,
                    active_error=active_error,
                )
