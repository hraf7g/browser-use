from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.models.tender import Tender
from src.shared.schemas.tender import (
    TenderListItem,
    TenderListQueryParams,
    TenderListResponse,
)
from src.shared.text.multilingual import normalize_multilingual_text


def list_tenders(
    session: Session,
    *,
    params: TenderListQueryParams,
) -> TenderListResponse:
    """Return a paginated list of tenders using validated query parameters."""
    filters = []

    if params.source_id is not None:
        filters.append(Tender.source_id == params.source_id)

    if params.search is not None:
        normalized_search = normalize_multilingual_text(params.search)
        if normalized_search:
            filters.append(Tender.search_text.ilike(f"%{normalized_search}%"))

    total_query = select(func.count()).select_from(Tender)
    if filters:
        total_query = total_query.where(*filters)

    total = session.execute(total_query).scalar_one()

    offset = (params.page - 1) * params.limit

    items_query = (
        select(Tender)
        .order_by(
            Tender.closing_date.asc(),
            Tender.created_at.desc(),
            Tender.id.asc(),
        )
        .offset(offset)
        .limit(params.limit)
    )

    if filters:
        items_query = items_query.where(*filters)

    tenders = session.execute(items_query).scalars().all()

    return TenderListResponse(
        items=[build_tender_list_item(tender) for tender in tenders],
        total=total,
        page=params.page,
        limit=params.limit,
    )


def build_tender_list_item(tender: Tender) -> TenderListItem:
    """Build a safe tenders list item response from the tender model."""
    return TenderListItem(
        id=tender.id,
        source_id=tender.source_id,
        source_url=tender.source_url,
        title=tender.title,
        issuing_entity=tender.issuing_entity,
        closing_date=tender.closing_date,
        category=tender.category,
        ai_summary=tender.ai_summary,
        tender_ref=tender.tender_ref,
    )
