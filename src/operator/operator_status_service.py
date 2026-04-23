from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from src.db.models.browser_agent_run import BrowserAgentRun
from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.shared.config.settings import get_settings
from src.shared.monitored_sources import MONITORED_SOURCE_NAMES, MONITORED_SOURCE_ORDER
from src.shared.schemas.operator_status import (
	OperatorBrowserAgentRuntimeStatus,
	OperatorSourceAIEnrichmentStatus,
	OperatorSourceStatusItem,
	OperatorStatusResponse,
)
from src.shared.source_registry import normalize_source_health_status


@dataclass(frozen=True)
class _SourceAIEnrichmentRollup:
	pending_count: int = 0
	retryable_failed_count: int = 0
	exhausted_count: int = 0
	completed_count: int = 0
	last_attempted_at: datetime | None = None
	last_generated_at: datetime | None = None
	last_error: str | None = None
	last_error_at: datetime | None = None


def list_operator_source_statuses(session: Session) -> OperatorStatusResponse:
	"""
	Return an operator-facing health snapshot for all monitored sources.

	Notes:
	    - This function is read-only.
	    - It does not commit the transaction.
	    - It prefers the latest crawl run by started_at desc, then id desc.
	"""
	sources: list[Source] = list(session.execute(select(Source).where(Source.name.in_(MONITORED_SOURCE_NAMES))).scalars().all())
	sources.sort(
		key=lambda source: (
			MONITORED_SOURCE_ORDER.get(source.name, len(MONITORED_SOURCE_ORDER)),
			source.id,
		)
	)

	if not sources:
		return OperatorStatusResponse(
			generated_at=datetime.now(timezone.utc),
			browser_agent_runtime=_build_browser_agent_runtime_status(session=session),
			sources=[],
		)

	source_ids = [source.id for source in sources]
	ai_enrichment_by_source_id = _build_ai_enrichment_rollups(
		session=session,
		source_ids=source_ids,
	)

	crawl_runs = (
		session.execute(
			select(CrawlRun)
			.where(CrawlRun.source_id.in_(source_ids))
			.order_by(
				CrawlRun.source_id.asc(),
				CrawlRun.started_at.desc(),
				CrawlRun.id.desc(),
			)
		)
		.scalars()
		.all()
	)

	latest_run_by_source_id: dict = {}
	for crawl_run in crawl_runs:
		if crawl_run.source_id not in latest_run_by_source_id:
			latest_run_by_source_id[crawl_run.source_id] = crawl_run

	items = [
		_build_operator_source_status_item(
			source=source,
			latest_run=latest_run_by_source_id.get(source.id),
			ai_enrichment=ai_enrichment_by_source_id.get(source.id, _SourceAIEnrichmentRollup()),
		)
		for source in sources
	]

	return OperatorStatusResponse(
		generated_at=datetime.now(timezone.utc),
		browser_agent_runtime=_build_browser_agent_runtime_status(session=session),
		sources=items,
	)


def _build_browser_agent_runtime_status(*, session: Session) -> OperatorBrowserAgentRuntimeStatus:
	"""Build an operator-facing snapshot of live browser-agent queue/runtime health."""
	settings = get_settings()
	now = datetime.now(UTC)
	day_ago = now - timedelta(hours=24)
	stale_cutoff = now - timedelta(seconds=settings.browser_agent_worker_stale_heartbeat_seconds)

	row = session.execute(
		select(
			func.sum(case((BrowserAgentRun.status == 'queued', 1), else_=0)).label('queued_count'),
			func.sum(case((BrowserAgentRun.status == 'running', 1), else_=0)).label('running_count'),
			func.sum(case((BrowserAgentRun.status == 'cancelling', 1), else_=0)).label('cancelling_count'),
			func.sum(
				case(
					(
						(BrowserAgentRun.status == 'completed') & (BrowserAgentRun.finished_at >= day_ago),
						1,
					),
					else_=0,
				)
			).label('completed_last_24h_count'),
			func.sum(
				case(
					(
						(BrowserAgentRun.status == 'failed') & (BrowserAgentRun.finished_at >= day_ago),
						1,
					),
					else_=0,
				)
			).label('failed_last_24h_count'),
			func.sum(
				case(
					(
						(BrowserAgentRun.status == 'cancelled') & (BrowserAgentRun.finished_at >= day_ago),
						1,
					),
					else_=0,
				)
			).label('cancelled_last_24h_count'),
			func.sum(
				case(
					(
						(BrowserAgentRun.status.in_(('running', 'cancelling')))
						& ((BrowserAgentRun.last_heartbeat_at.is_(None)) | (BrowserAgentRun.last_heartbeat_at <= stale_cutoff)),
						1,
					),
					else_=0,
				)
			).label('stale_running_count'),
			func.min(case((BrowserAgentRun.status == 'queued', BrowserAgentRun.queued_at), else_=None)).label('oldest_queued_at'),
			func.max(BrowserAgentRun.started_at).label('latest_started_at'),
			func.max(BrowserAgentRun.finished_at).label('latest_finished_at'),
		)
	).one()

	return OperatorBrowserAgentRuntimeStatus(
		queued_count=int(row.queued_count or 0),
		running_count=int(row.running_count or 0),
		cancelling_count=int(row.cancelling_count or 0),
		completed_last_24h_count=int(row.completed_last_24h_count or 0),
		failed_last_24h_count=int(row.failed_last_24h_count or 0),
		cancelled_last_24h_count=int(row.cancelled_last_24h_count or 0),
		stale_running_count=int(row.stale_running_count or 0),
		oldest_queued_at=row.oldest_queued_at,
		latest_started_at=row.latest_started_at,
		latest_finished_at=row.latest_finished_at,
		max_global_running_runs=settings.browser_agent_max_global_running_runs,
		worker_stale_heartbeat_seconds=settings.browser_agent_worker_stale_heartbeat_seconds,
	)


def _build_operator_source_status_item(
	*,
	source: Source,
	latest_run: CrawlRun | None,
	ai_enrichment: _SourceAIEnrichmentRollup,
) -> OperatorSourceStatusItem:
	"""Build one operator source status item."""
	return OperatorSourceStatusItem(
		source_id=source.id,
		source_name=source.name,
		source_base_url=source.base_url,
		source_country_code=source.country_code,
		source_country_name=source.country_name,
		source_lifecycle=source.lifecycle,
		source_status=normalize_source_health_status(source.status),
		failure_count=source.failure_count,
		last_successful_run_at=source.last_successful_run_at,
		last_failed_run_at=source.last_failed_run_at,
		latest_run_id=None if latest_run is None else latest_run.id,
		latest_run_status=None if latest_run is None else latest_run.status,
		latest_run_started_at=None if latest_run is None else latest_run.started_at,
		latest_run_finished_at=None if latest_run is None else latest_run.finished_at,
		latest_run_new_tenders_count=(None if latest_run is None else latest_run.new_tenders_count),
		latest_run_crawled_row_count=(None if latest_run is None else latest_run.crawled_row_count),
		latest_run_normalized_row_count=(None if latest_run is None else latest_run.normalized_row_count),
		latest_run_accepted_row_count=(None if latest_run is None else latest_run.accepted_row_count),
		latest_run_review_required_row_count=(None if latest_run is None else latest_run.review_required_row_count),
		latest_run_updated_tender_count=(None if latest_run is None else latest_run.updated_tender_count),
		latest_run_failure_reason=(None if latest_run is None else latest_run.failure_reason),
		latest_run_failure_step=(None if latest_run is None else latest_run.failure_step),
		latest_run_identifier=(None if latest_run is None else latest_run.run_identifier),
		ai_enrichment=OperatorSourceAIEnrichmentStatus(
			pending_count=ai_enrichment.pending_count,
			retryable_failed_count=ai_enrichment.retryable_failed_count,
			exhausted_count=ai_enrichment.exhausted_count,
			completed_count=ai_enrichment.completed_count,
			last_attempted_at=ai_enrichment.last_attempted_at,
			last_generated_at=ai_enrichment.last_generated_at,
			last_error=ai_enrichment.last_error,
			last_error_at=ai_enrichment.last_error_at,
		),
	)


def _build_ai_enrichment_rollups(
	*,
	session: Session,
	source_ids: list,
) -> dict:
	"""Build per-source AI enrichment telemetry without loading all tenders into memory."""
	if not source_ids:
		return {}

	max_attempts = get_settings().ai_summary_max_attempts

	rollup_rows = session.execute(
		select(
			Tender.source_id,
			func.sum(
				case(
					(
						(Tender.ai_summary.is_(None)) & (Tender.ai_summary_attempt_count == 0),
						1,
					),
					else_=0,
				)
			).label('pending_count'),
			func.sum(
				case(
					(
						(Tender.ai_summary.is_(None))
						& (Tender.ai_summary_attempt_count > 0)
						& (Tender.ai_summary_attempt_count < max_attempts),
						1,
					),
					else_=0,
				)
			).label('retryable_failed_count'),
			func.sum(
				case(
					(
						(Tender.ai_summary.is_(None)) & (Tender.ai_summary_attempt_count >= max_attempts),
						1,
					),
					else_=0,
				)
			).label('exhausted_count'),
			func.sum(
				case(
					(
						Tender.ai_summary.is_not(None),
						1,
					),
					else_=0,
				)
			).label('completed_count'),
			func.max(Tender.ai_summary_last_attempted_at).label('last_attempted_at'),
			func.max(Tender.ai_summary_generated_at).label('last_generated_at'),
		)
		.where(Tender.source_id.in_(source_ids))
		.group_by(Tender.source_id)
	).all()

	latest_error_rows = session.execute(
		select(
			Tender.source_id,
			Tender.ai_summary_last_error,
			Tender.ai_summary_last_attempted_at,
		)
		.where(
			Tender.source_id.in_(source_ids),
			Tender.ai_summary_last_error.is_not(None),
		)
		.order_by(
			Tender.source_id.asc(),
			Tender.ai_summary_last_attempted_at.desc(),
			Tender.id.desc(),
		)
	).all()

	latest_error_by_source_id: dict = {}
	for row in latest_error_rows:
		if row.source_id not in latest_error_by_source_id:
			latest_error_by_source_id[row.source_id] = row

	rollups: dict = {}
	for row in rollup_rows:
		latest_error_row = latest_error_by_source_id.get(row.source_id)
		rollups[row.source_id] = _SourceAIEnrichmentRollup(
			pending_count=int(row.pending_count or 0),
			retryable_failed_count=int(row.retryable_failed_count or 0),
			exhausted_count=int(row.exhausted_count or 0),
			completed_count=int(row.completed_count or 0),
			last_attempted_at=row.last_attempted_at,
			last_generated_at=row.last_generated_at,
			last_error=(None if latest_error_row is None else latest_error_row.ai_summary_last_error),
			last_error_at=(None if latest_error_row is None else latest_error_row.ai_summary_last_attempted_at),
		)

	return rollups
