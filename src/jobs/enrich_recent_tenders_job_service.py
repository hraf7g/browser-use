from __future__ import annotations

from datetime import datetime

from src.ai.tender_enrichment_service import (
	TenderEnrichmentResult,
	enrich_tenders_updated_since,
)
from src.db.session import get_session_factory
from src.jobs.job_lock_service import acquire_named_job_lock, finalize_named_job_lock
from src.shared.logging.logger import get_logger

ENRICH_RECENT_TENDERS_JOB_LOCK_NAME = 'utw:enrich_recent_tenders_job'
logger = get_logger(__name__)


class EnrichRecentTendersJobAlreadyRunningError(RuntimeError):
	"""Raised when another session already holds the recent-enrichment job lock."""


def run_enrich_recent_tenders_job(
	*,
	since: datetime,
) -> TenderEnrichmentResult:
	"""
	Execute one persisted recent-tender AI enrichment job.

	Notes:
		- Opens its own database session.
		- Acquires a DB advisory lock before enrichment.
		- Commits on success.
		- Rolls back and re-raises unexpected exceptions.
	"""
	session_factory = get_session_factory()

	with session_factory() as session:
		lock_acquired = False
		active_error: Exception | None = None
		try:
			lock_acquired = acquire_named_job_lock(
				session,
				job_name=ENRICH_RECENT_TENDERS_JOB_LOCK_NAME,
			)
			if not lock_acquired:
				raise EnrichRecentTendersJobAlreadyRunningError(
					'recent-tenders enrichment job is already running in another session'
				)

			result = enrich_tenders_updated_since(
				session,
				since=since,
			)
			session.commit()
			return result
		except Exception as exc:
			active_error = exc
			session.rollback()
			raise
		finally:
			if lock_acquired:
				finalize_named_job_lock(
					session,
					job_name=ENRICH_RECENT_TENDERS_JOB_LOCK_NAME,
					logger=logger,
					active_error=active_error,
				)
