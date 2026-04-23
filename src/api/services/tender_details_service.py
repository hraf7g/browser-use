from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.shared.schemas.tender_details import (
	TenderDetailsNotificationState,
	TenderDetailsResponse,
	TenderDetailsTimelineItem,
)


class TenderDetailsNotFoundError(ValueError):
	"""Raised when a requested tender cannot be found."""


def get_tender_details(
	session: Session,
	*,
	user_id: UUID,
	tender_id: UUID,
) -> TenderDetailsResponse:
	"""Return a safe user-facing tender detail payload."""
	tender = session.get(Tender, tender_id)
	if tender is None:
		raise TenderDetailsNotFoundError(f"tender '{tender_id}' was not found")

	source = session.get(Source, tender.source_id)
	match = session.execute(
		select(TenderMatch).where(
			TenderMatch.user_id == user_id,
			TenderMatch.tender_id == tender.id,
		)
	).scalar_one_or_none()

	latest_successful_run = None
	if source is not None:
		latest_successful_run = (
			session.execute(
				select(CrawlRun)
				.where(
					CrawlRun.source_id == source.id,
					CrawlRun.status == 'success',
				)
				.order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc())
			)
			.scalars()
			.first()
		)

	notification_state = TenderDetailsNotificationState(
		match_created_at=None if match is None else match.created_at,
		matched_keywords=[] if match is None else list(match.matched_keywords or []),
		matched_country_codes=[] if match is None else list(match.matched_country_codes or []),
		matched_industry_codes=[] if match is None else list(match.matched_industry_codes or []),
		instant_alert_sent=False if match is None else match.alerted_at is not None,
		instant_alert_sent_at=None if match is None else match.alerted_at,
		daily_brief_sent=False if match is None else match.sent_at is not None,
		daily_brief_sent_at=None if match is None else match.sent_at,
	)

	activity_timeline = _build_activity_timeline(
		tender=tender,
		source=source,
		match=match,
		latest_successful_run=latest_successful_run,
	)

	return TenderDetailsResponse(
		id=tender.id,
		title=tender.title,
		issuing_entity=tender.issuing_entity,
		source_id=tender.source_id,
		source_name=None if source is None else source.name,
		source_url=tender.source_url,
		closing_date=tender.closing_date,
		opening_date=tender.opening_date,
		published_at=tender.published_at,
		tender_ref=tender.tender_ref,
		category=tender.category,
		industry_codes=list(tender.industry_codes or []),
		primary_industry_code=tender.primary_industry_code,
		ai_summary=tender.ai_summary,
		matched_keywords=[] if match is None else list(match.matched_keywords or []),
		matched_country_codes=[] if match is None else list(match.matched_country_codes or []),
		matched_industry_codes=[] if match is None else list(match.matched_industry_codes or []),
		notification_state=notification_state,
		activity_timeline=activity_timeline,
	)


def _build_activity_timeline(
	*,
	tender: Tender,
	source: Source | None,
	match: TenderMatch | None,
	latest_successful_run: CrawlRun | None,
) -> list[TenderDetailsTimelineItem]:
	"""Build a deterministic timeline using only persisted facts."""
	items: list[TenderDetailsTimelineItem] = []

	if latest_successful_run is not None:
		checked_at = latest_successful_run.finished_at or latest_successful_run.started_at
		items.append(
			TenderDetailsTimelineItem(
				id=f'source-checked:{checked_at.isoformat()}',
				kind='source_checked',
				status='healthy',
				timestamp=checked_at,
				title='Source checked',
				summary=(f'{source.name if source is not None else "Source"} completed a successful crawl run.'),
			)
		)

	items.append(
		TenderDetailsTimelineItem(
			id=f'tender-detected:{tender.id}',
			kind='tender_detected',
			status='info',
			timestamp=tender.created_at,
			title='Tender available',
			summary='The tender was ingested and made available in the platform.',
		)
	)

	if match is not None:
		items.append(
			TenderDetailsTimelineItem(
				id=f'match-created:{match.id}',
				kind='match_created',
				status='info',
				timestamp=match.created_at,
				title='Match created',
				summary=_build_match_summary(
					matched_keywords=list(match.matched_keywords or []),
					matched_country_codes=list(match.matched_country_codes or []),
					matched_industry_codes=list(match.matched_industry_codes or []),
				),
			)
		)

		if match.alerted_at is not None:
			items.append(
				TenderDetailsTimelineItem(
					id=f'instant-alert:{match.id}',
					kind='instant_alert_sent',
					status='sent',
					timestamp=match.alerted_at,
					title='Instant alert sent',
					summary='The tender was included in an instant alert delivery.',
				)
			)

		if match.sent_at is not None:
			items.append(
				TenderDetailsTimelineItem(
					id=f'daily-brief:{match.id}',
					kind='daily_brief_sent',
					status='sent',
					timestamp=match.sent_at,
					title='Daily brief sent',
					summary='The tender was included in a daily brief delivery.',
				)
			)

	items.sort(
		key=lambda item: (
			item.timestamp,
			_timeline_priority(item.kind),
			item.title,
		),
		reverse=True,
	)
	return items


def _build_match_summary(
	*,
	matched_keywords: list[str],
	matched_country_codes: list[str],
	matched_industry_codes: list[str],
) -> str:
	"""Return a compact summary for the persisted deterministic match evidence."""
	parts: list[str] = []
	if matched_country_codes:
		parts.append(f'Matched countries: {", ".join(matched_country_codes)}.')
	if matched_industry_codes:
		parts.append(f'Matched industries: {", ".join(matched_industry_codes)}.')
	if matched_keywords:
		parts.append(f'Matched keywords: {", ".join(matched_keywords)}.')

	if not parts:
		return 'The tender matched the saved monitoring profile.'

	return ' '.join(parts)


def _timeline_priority(kind: str) -> int:
	"""Provide a deterministic order for same-timestamp timeline items."""
	order = {
		'daily_brief_sent': 5,
		'instant_alert_sent': 4,
		'match_created': 3,
		'tender_detected': 2,
		'source_checked': 1,
	}
	return order.get(kind, 0)
