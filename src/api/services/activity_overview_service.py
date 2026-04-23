from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.shared.monitored_sources import MONITORED_SOURCE_NAMES, MONITORED_SOURCE_ORDER
from src.shared.schemas.activity_overview import (
	ActivityFeedItem,
	ActivityOverviewResponse,
	ActivityOverviewSummary,
	ActivityRecentRunItem,
	ActivitySourceCard,
)
from src.shared.source_registry import normalize_source_health_status


def get_activity_overview(
	session: Session,
	*,
	user_id: UUID,
) -> ActivityOverviewResponse:
	"""Return a safe user-facing activity and source-monitoring overview."""
	sources: list[Source] = list(session.execute(select(Source).where(Source.name.in_(MONITORED_SOURCE_NAMES))).scalars().all())
	sources.sort(
		key=lambda source: (
			MONITORED_SOURCE_ORDER.get(source.name, len(MONITORED_SOURCE_ORDER)),
			source.id,
		)
	)

	source_ids = [source.id for source in sources]
	latest_run_by_source_id = _get_latest_run_by_source_id(
		session=session,
		source_ids=source_ids,
	)

	recent_runs = _get_recent_runs(session=session, source_ids=source_ids)
	match_rows = _get_recent_user_match_rows(session=session, user_id=user_id)

	sources_response = [
		_build_source_card(
			source=source,
			latest_run=latest_run_by_source_id.get(source.id),
		)
		for source in sources
	]

	summary = _build_summary(sources=sources)
	recent_activity_items = _build_activity_items(
		recent_runs=recent_runs,
		match_rows=match_rows,
	)

	return ActivityOverviewResponse(
		generated_at=datetime.now(timezone.utc),
		summary=summary,
		sources=sources_response,
		recent_runs=[
			ActivityRecentRunItem(
				id=run.id,
				source_id=run.source_id,
				source_name=source.name,
				status=run.status,
				started_at=run.started_at,
				finished_at=run.finished_at,
				new_tenders_count=run.new_tenders_count,
				failure_reason=run.failure_reason,
			)
			for run, source in recent_runs
		],
		activity_items=recent_activity_items,
	)


def _build_summary(*, sources: list[Source]) -> ActivityOverviewSummary:
	"""Aggregate source health counts for the user-facing overview."""
	healthy = 0
	degraded = 0
	latest_successful_check_at = None

	for source in sources:
		status = normalize_source_health_status(source.status)
		if status == 'healthy':
			healthy += 1
		else:
			degraded += 1

		if source.last_successful_run_at is not None:
			if latest_successful_check_at is None or source.last_successful_run_at > latest_successful_check_at:
				latest_successful_check_at = source.last_successful_run_at

	return ActivityOverviewSummary(
		total_sources=len(sources),
		healthy_sources=healthy,
		degraded_sources=degraded,
		latest_successful_check_at=latest_successful_check_at,
	)


def _get_latest_run_by_source_id(
	*,
	session: Session,
	source_ids: list[UUID],
) -> dict[UUID, CrawlRun]:
	"""Return the latest crawl run per source in deterministic order."""
	if not source_ids:
		return {}

	rows = (
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

	latest_by_source_id: dict[UUID, CrawlRun] = {}
	for run in rows:
		if run.source_id not in latest_by_source_id:
			latest_by_source_id[run.source_id] = run

	return latest_by_source_id


def _get_recent_runs(
	*,
	session: Session,
	source_ids: list[UUID],
) -> list[tuple[CrawlRun, Source]]:
	"""Return recent crawl runs paired with their source."""
	if not source_ids:
		return []

	rows = session.execute(
		select(CrawlRun, Source)
		.join(Source, Source.id == CrawlRun.source_id)
		.where(CrawlRun.source_id.in_(source_ids))
		.order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc())
		.limit(10)
	).all()
	return [(run, source) for run, source in rows]


def _get_recent_user_match_rows(
	*,
	session: Session,
	user_id: UUID,
) -> list[tuple[TenderMatch, Tender, Source]]:
	"""Return the user's recent tender matches with their tender and source."""
	rows = session.execute(
		select(TenderMatch, Tender, Source)
		.join(Tender, Tender.id == TenderMatch.tender_id)
		.join(Source, Source.id == Tender.source_id)
		.where(TenderMatch.user_id == user_id)
		.order_by(TenderMatch.created_at.desc(), TenderMatch.id.desc())
		.limit(10)
	).all()
	return [(match, tender, source) for match, tender, source in rows]


def _build_source_card(*, source: Source, latest_run: CrawlRun | None) -> ActivitySourceCard:
	"""Build one user-facing source monitoring card."""
	return ActivitySourceCard(
		source_id=source.id,
		source_name=source.name,
		source_country_code=source.country_code,
		source_country_name=source.country_name,
		source_lifecycle=source.lifecycle,
		source_status=normalize_source_health_status(source.status),
		failure_count=source.failure_count,
		last_successful_run_at=source.last_successful_run_at,
		last_failed_run_at=source.last_failed_run_at,
		latest_run_status=None if latest_run is None else latest_run.status,
		latest_run_started_at=None if latest_run is None else latest_run.started_at,
		latest_run_finished_at=None if latest_run is None else latest_run.finished_at,
		latest_run_new_tenders_count=(None if latest_run is None else latest_run.new_tenders_count),
		latest_run_updated_tender_count=(None if latest_run is None else latest_run.updated_tender_count),
		latest_run_crawled_row_count=(None if latest_run is None else latest_run.crawled_row_count),
		latest_run_normalized_row_count=(None if latest_run is None else latest_run.normalized_row_count),
		latest_run_accepted_row_count=(None if latest_run is None else latest_run.accepted_row_count),
		latest_run_review_required_row_count=(None if latest_run is None else latest_run.review_required_row_count),
		latest_run_failure_step=(None if latest_run is None else latest_run.failure_step),
		latest_run_failure_reason=(None if latest_run is None else latest_run.failure_reason),
	)


def _build_activity_items(
	*,
	recent_runs: list[tuple[CrawlRun, Source]],
	match_rows: list[tuple[TenderMatch, Tender, Source]],
) -> list[ActivityFeedItem]:
	"""Build recent activity items from persisted user and system facts."""
	items: list[ActivityFeedItem] = []

	for run, source in recent_runs:
		if run.status == 'failed':
			items.append(
				ActivityFeedItem(
					id=f'run-failed:{run.id}',
					kind='source_failed',
					status='failed',
					timestamp=run.finished_at or run.started_at,
					title='Source run failed',
					summary=_build_run_summary(run=run, source_name=source.name),
					source_id=source.id,
					source_name=source.name,
					metadata={
						'run_id': str(run.id),
						'new_tenders_count': run.new_tenders_count,
						'failure_reason': run.failure_reason,
					},
				)
			)
		else:
			items.append(
				ActivityFeedItem(
					id=f'run-success:{run.id}',
					kind='source_checked',
					status='healthy',
					timestamp=run.finished_at or run.started_at,
					title='Source checked',
					summary=_build_run_summary(run=run, source_name=source.name),
					source_id=source.id,
					source_name=source.name,
					metadata={
						'run_id': str(run.id),
						'new_tenders_count': run.new_tenders_count,
					},
				)
			)

	for match, tender, source in match_rows:
		keywords = list(match.matched_keywords or [])
		matched_country_codes = list(match.matched_country_codes or [])
		matched_industry_codes = list(match.matched_industry_codes or [])
		items.append(
			ActivityFeedItem(
				id=f'match-created:{match.id}',
				kind='match_created',
				status='info',
				timestamp=match.created_at,
				title='Match created',
				summary=_build_match_summary(
					tender_title=tender.title,
					keywords=keywords,
					matched_country_codes=matched_country_codes,
					matched_industry_codes=matched_industry_codes,
				),
				source_id=source.id,
				source_name=source.name,
				tender_id=tender.id,
				tender_title=tender.title,
				matched_keywords=keywords,
				matched_country_codes=matched_country_codes,
				matched_industry_codes=matched_industry_codes,
				metadata={
					'match_id': str(match.id),
					'closing_date': None if tender.closing_date is None else tender.closing_date.isoformat(),
					'matched_country_codes': matched_country_codes,
					'matched_industry_codes': matched_industry_codes,
				},
			)
		)

		if match.alerted_at is not None:
			items.append(
				ActivityFeedItem(
					id=f'instant-alert:{match.id}',
					kind='instant_alert_sent',
					status='sent',
					timestamp=match.alerted_at,
					title='Instant alert sent',
					summary=_build_delivery_summary(
						tender_title=tender.title,
						delivery_label='instant alert',
					),
					source_id=source.id,
					source_name=source.name,
					tender_id=tender.id,
					tender_title=tender.title,
					matched_keywords=keywords,
					matched_country_codes=matched_country_codes,
					matched_industry_codes=matched_industry_codes,
					metadata={
						'match_id': str(match.id),
						'delivery_type': 'instant_alert',
						'matched_country_codes': matched_country_codes,
						'matched_industry_codes': matched_industry_codes,
					},
				)
			)

		if match.sent_at is not None:
			items.append(
				ActivityFeedItem(
					id=f'daily-brief:{match.id}',
					kind='daily_brief_sent',
					status='sent',
					timestamp=match.sent_at,
					title='Daily brief sent',
					summary=_build_delivery_summary(
						tender_title=tender.title,
						delivery_label='daily brief',
					),
					source_id=source.id,
					source_name=source.name,
					tender_id=tender.id,
					tender_title=tender.title,
					matched_keywords=keywords,
					matched_country_codes=matched_country_codes,
					matched_industry_codes=matched_industry_codes,
					metadata={
						'match_id': str(match.id),
						'delivery_type': 'daily_brief',
						'matched_country_codes': matched_country_codes,
						'matched_industry_codes': matched_industry_codes,
					},
				)
			)

	items.sort(
		key=lambda item: (
			item.timestamp,
			_activity_priority(item.kind),
			item.id,
		),
		reverse=True,
	)
	return items


def _build_run_summary(*, run: CrawlRun, source_name: str) -> str:
	"""Build a compact summary for a crawl run activity item."""
	if run.status == 'failed':
		if run.failure_reason:
			return f'{source_name} failed: {run.failure_reason}'
		return f'{source_name} encountered a crawl failure.'

	if run.new_tenders_count is not None:
		tender_word = 'tender' if run.new_tenders_count == 1 else 'tenders'
		return f'{source_name} completed successfully and found {run.new_tenders_count} new {tender_word}.'

	return f'{source_name} completed a successful crawl run.'


def _build_match_summary(
	*,
	tender_title: str,
	keywords: list[str],
	matched_country_codes: list[str],
	matched_industry_codes: list[str],
) -> str:
	"""Build a compact match summary for the activity feed."""
	reason_parts: list[str] = []
	if matched_country_codes:
		reason_parts.append(f'countries {", ".join(matched_country_codes)}')
	if matched_industry_codes:
		reason_parts.append(f'industries {", ".join(matched_industry_codes)}')
	if keywords:
		reason_parts.append(f'keywords {", ".join(keywords)}')

	if reason_parts:
		return f'{tender_title} matched on {", ".join(reason_parts)}.'
	return f"{tender_title} matched the user's profile."


def _build_delivery_summary(*, tender_title: str, delivery_label: str) -> str:
	"""Build a compact delivery summary for the activity feed."""
	return f'{tender_title} was included in a {delivery_label} delivery.'


def _activity_priority(kind: str) -> int:
	"""Provide a deterministic order for same-timestamp activity items."""
	order = {
		'daily_brief_sent': 5,
		'instant_alert_sent': 4,
		'match_created': 3,
		'source_failed': 2,
		'source_checked': 1,
	}
	return order.get(kind, 0)
