from __future__ import annotations

from datetime import datetime

from src.db.session import get_session_factory
from src.jobs.job_lock_service import acquire_named_job_lock, release_named_job_lock
from src.matching.tender_matching_service import match_tenders_updated_since

MATCH_RECENT_TENDERS_JOB_LOCK_NAME = "utw:match_recent_tenders_job"


class MatchRecentTendersJobAlreadyRunningError(RuntimeError):
    """Raised when another session already holds the recent-matching job lock."""


def run_match_recent_tenders_job(
    *,
    since: datetime,
) -> int:
    """
    Execute one persisted recent-tender matching job.

    Notes:
        - Opens its own database session.
        - Acquires a DB advisory lock before matching.
        - Commits on success.
        - Rolls back and re-raises unexpected exceptions.
    """
    session_factory = get_session_factory()

    with session_factory() as session:
        lock_acquired = False
        try:
            lock_acquired = acquire_named_job_lock(
                session,
                job_name=MATCH_RECENT_TENDERS_JOB_LOCK_NAME,
            )
            if not lock_acquired:
                raise MatchRecentTendersJobAlreadyRunningError(
                    "recent-tenders matching job is already running in another session"
                )

            matches_created = match_tenders_updated_since(
                session,
                since=since,
            )
            session.commit()
            return matches_created
        except Exception:
            session.rollback()
            raise
        finally:
            if lock_acquired:
                released = release_named_job_lock(
                    session,
                    job_name=MATCH_RECENT_TENDERS_JOB_LOCK_NAME,
                )
                if not released:
                    raise RuntimeError(
                        "expected recent-tenders job lock release to succeed"
                    )
