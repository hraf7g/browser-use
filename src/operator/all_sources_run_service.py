from __future__ import annotations

from datetime import UTC, datetime
from logging import Logger

from sqlalchemy.orm import Session, sessionmaker

from src.jobs.enrich_recent_tenders_job_service import (
    EnrichRecentTendersJobAlreadyRunningError,
    run_enrich_recent_tenders_job,
)
from src.operator.source_run_dispatch_service import dispatch_source_run
from src.shared.logging.logger import get_logger
from src.shared.schemas.operator_run import OperatorRunSourceResponse
from src.shared.schemas.operator_run_batch import OperatorRunAllSourcesResponse
from src.shared.source_registry import MONITORED_SOURCE_NAMES

SUPPORTED_SOURCE_RUN_ORDER: tuple[str, ...] = MONITORED_SOURCE_NAMES
logger: Logger = get_logger(__name__)


def run_all_supported_sources(
    *,
    session: Session,
) -> OperatorRunAllSourcesResponse:
    """
    Run all supported sources sequentially in deterministic order.

    Notes:
        - This service does not commit the transaction.
        - The caller owns transaction boundaries.
        - Runs are intentionally sequential for deterministic operational
          behavior and simpler auditability.
        - One source failure does not prevent later sources from running.
    """
    started_at = datetime.now(UTC)
    results: list[OperatorRunSourceResponse] = []

    for source_name in SUPPORTED_SOURCE_RUN_ORDER:
        result = dispatch_source_run(
            session=session,
            source_name=source_name,
        )
        results.append(result)

    return _build_batch_response(
        started_at=started_at,
        results=results,
    )


def run_all_supported_sources_with_isolated_transactions(
	*,
	session_factory: sessionmaker[Session],
) -> OperatorRunAllSourcesResponse:
	"""
	Run all supported sources sequentially with one transaction per source.

	Notes:
		- Each source runs in its own database session.
		- Each source result is committed independently after that source finishes.
		- A later unexpected failure does not roll back already persisted earlier runs.
		- Source-specific failed results still persist because source run services
		  return structured failure results instead of raising for expected source failures.
	"""
	started_at = datetime.now(UTC)
	results: list[OperatorRunSourceResponse] = []

	for source_name in SUPPORTED_SOURCE_RUN_ORDER:
		with session_factory() as session:
			try:
				result = dispatch_source_run(
					session=session,
					source_name=source_name,
				)
				session.commit()
			except Exception:
				session.rollback()
				raise

		results.append(result)

	_try_run_post_ingestion_enrichment(
		started_at=started_at,
	)

	return _build_batch_response(
		started_at=started_at,
		results=results,
	)


def _try_run_post_ingestion_enrichment(*, started_at: datetime) -> None:
	"""Run AI enrichment after source ingestion without blocking the core crawl batch."""
	try:
		result = run_enrich_recent_tenders_job(since=started_at)
	except EnrichRecentTendersJobAlreadyRunningError:
		logger.warning(
			'recent_tender_ai_enrichment_skipped reason=already_running '
			f'since={started_at.isoformat()}'
		)
	except Exception:
		logger.exception(
			'recent_tender_ai_enrichment_failed '
			f'since={started_at.isoformat()}'
		)
	else:
		logger.info(
			'recent_tender_ai_enrichment_finished '
			f'since={started_at.isoformat()} '
			f'attempted_count={result.attempted_count} '
			f'enriched_count={result.enriched_count} '
			f'failed_count={result.failed_count} '
			f'skipped_count={result.skipped_count}'
		)


def _build_batch_response(
    *,
    started_at: datetime,
    results: list[OperatorRunSourceResponse],
) -> OperatorRunAllSourcesResponse:
    """Build the deterministic batch response from ordered source results."""
    finished_at = datetime.now(UTC)
    success_count = sum(1 for result in results if result.status == "success")
    failed_count = len(results) - success_count

    if failed_count == 0:
        overall_status = "success"
    elif success_count == 0:
        overall_status = "failed"
    else:
        overall_status = "partial_failure"

    return OperatorRunAllSourcesResponse(
        started_at=started_at,
        finished_at=finished_at,
        overall_status=overall_status,
        total_sources=len(results),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    )
