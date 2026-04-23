from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.shared.monitored_sources import MONITORED_SOURCE_ORDER
from src.shared.schemas.tender import (
	TenderListItem,
	TenderListQueryParams,
	TenderListResponse,
	TenderListSourceOption,
)
from src.shared.text.multilingual import normalize_multilingual_text


def list_tenders(
	session: Session,
	*,
	user_id: UUID,
	params: TenderListQueryParams,
) -> TenderListResponse:
	"""Return a paginated list of tenders using validated query parameters."""
	filters = []
	now = datetime.now(timezone.utc)
	tender_match = aliased(TenderMatch)

	if params.source_id is not None:
		filters.append(Tender.source_id == params.source_id)

	if params.source_ids:
		filters.append(Tender.source_id.in_(params.source_ids))

	if params.search is not None:
		normalized_search = normalize_multilingual_text(params.search)
		if normalized_search:
			filters.append(Tender.search_text.like(f'%{normalized_search}%'))

	if params.match_only:
		filters.append(tender_match.id.is_not(None))

	if params.new_only:
		filters.append(Tender.created_at >= now - timedelta(days=14))

	if params.closing_soon:
		filters.append(Tender.closing_date.is_not(None))
		filters.append(Tender.closing_date >= now)
		filters.append(Tender.closing_date <= now + timedelta(days=7))

	base_query = (
		select(
			Tender,
			Source.name.label('source_name'),
			tender_match.id.label('match_id'),
			tender_match.matched_keywords.label('matched_keywords'),
			tender_match.matched_country_codes.label('matched_country_codes'),
			tender_match.matched_industry_codes.label('matched_industry_codes'),
		)
		.join(Source, Source.id == Tender.source_id)
		.outerjoin(
			tender_match,
			(tender_match.tender_id == Tender.id) & (tender_match.user_id == user_id),
		)
	)

	if filters:
		base_query = base_query.where(*filters)

	total = session.execute(
		select(func.count()).select_from(base_query.with_only_columns(Tender.id).distinct().subquery())
	).scalar_one()

	available_sources = [
		TenderListSourceOption(id=source_id, name=source_name)
		for source_id, source_name in sorted(
			session.execute(select(Source.id, Source.name).join(Tender, Tender.source_id == Source.id).distinct()).all(),
			key=lambda row: (
				MONITORED_SOURCE_ORDER.get(row.name, len(MONITORED_SOURCE_ORDER)),
				row.name,
				row.id,
			),
		)
	]

	offset = (params.page - 1) * params.limit

	rows = session.execute(base_query.order_by(*_build_sort_order(params=params)).offset(offset).limit(params.limit)).all()

	return TenderListResponse(
		items=[
			build_tender_list_item(
				tender=tender,
				source_name=source_name,
				is_matched=match_id is not None,
				matched_keywords=matched_keywords,
				matched_country_codes=matched_country_codes,
				matched_industry_codes=matched_industry_codes,
			)
			for tender, source_name, match_id, matched_keywords, matched_country_codes, matched_industry_codes in rows
		],
		available_sources=available_sources,
		total=total,
		page=params.page,
		limit=params.limit,
	)


def build_tender_list_item(
	tender: Tender,
	*,
	source_name: str,
	is_matched: bool,
	matched_keywords: list[str] | None,
	matched_country_codes: list[str] | None,
	matched_industry_codes: list[str] | None,
) -> TenderListItem:
	"""Build a safe tenders list item response from the tender model."""
	return TenderListItem(
		id=tender.id,
		source_id=tender.source_id,
		source_name=source_name,
		source_url=tender.source_url,
		title=tender.title,
		issuing_entity=tender.issuing_entity,
		closing_date=tender.closing_date,
		created_at=tender.created_at,
		category=tender.category,
		industry_codes=list(tender.industry_codes or []),
		primary_industry_code=tender.primary_industry_code,
		ai_summary=tender.ai_summary,
		tender_ref=tender.tender_ref,
		is_matched=is_matched,
		matched_keywords=list(matched_keywords or []),
		matched_country_codes=list(matched_country_codes or []),
		matched_industry_codes=list(matched_industry_codes or []),
	)


def _build_sort_order(*, params: TenderListQueryParams):
	"""Return deterministic ordering for tender discovery."""
	if params.sort == 'newest':
		return (
			Tender.created_at.desc(),
			Tender.closing_date.asc().nulls_last(),
			Tender.id.asc(),
		)

	if params.sort == 'closingSoon':
		return (
			Tender.closing_date.asc().nulls_last(),
			Tender.created_at.desc(),
			Tender.id.asc(),
		)

	return (
		Tender.closing_date.asc().nulls_last(),
		Tender.created_at.desc(),
		Tender.id.asc(),
	)
