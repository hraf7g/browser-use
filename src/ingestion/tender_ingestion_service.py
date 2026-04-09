from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.tender import Tender
from src.shared.schemas.tender_ingestion import TenderIngestionInput
from src.shared.text.multilingual import normalize_multilingual_text


def ingest_tender(
    session: Session,
    *,
    payload: TenderIngestionInput,
) -> tuple[Tender, bool]:
    """
    Insert or update one tender deterministically.

    Returns:
        tuple[Tender, bool]:
            - Tender model instance
            - bool created flag (True if inserted, False if updated)

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
        - The dedupe key is the authoritative identity within a source.
        - search_text is persisted in normalized multilingual form for backend search.
    """
    existing_tender = session.execute(
        select(Tender).where(
            Tender.source_id == payload.source_id,
            Tender.dedupe_key == payload.dedupe_key,
        )
    ).scalar_one_or_none()

    search_text = _build_tender_search_text(payload)

    if existing_tender is None:
        tender = Tender(
            source_id=payload.source_id,
            tender_ref=payload.tender_ref,
            source_url=payload.source_url,
            title=payload.title,
            issuing_entity=payload.issuing_entity,
            closing_date=payload.closing_date,
            opening_date=payload.opening_date,
            published_at=payload.published_at,
            category=payload.category,
            ai_summary=payload.ai_summary,
            dedupe_key=payload.dedupe_key,
            search_text=search_text,
        )
        session.add(tender)
        session.flush()
        return tender, True

    existing_tender.tender_ref = payload.tender_ref
    existing_tender.source_url = payload.source_url
    existing_tender.title = payload.title
    existing_tender.issuing_entity = payload.issuing_entity
    existing_tender.closing_date = payload.closing_date
    existing_tender.opening_date = payload.opening_date
    existing_tender.published_at = payload.published_at
    existing_tender.category = payload.category
    existing_tender.ai_summary = payload.ai_summary
    existing_tender.search_text = search_text

    session.flush()
    return existing_tender, False


def _build_tender_search_text(payload: TenderIngestionInput) -> str:
    """Build deterministic persisted multilingual search text."""
    parts = [
        payload.title,
        payload.issuing_entity,
        payload.category,
        payload.ai_summary,
        payload.tender_ref,
    ]
    normalized_parts = [
        normalize_multilingual_text(part)
        for part in parts
        if isinstance(part, str) and part.strip()
    ]
    return " ".join(part for part in normalized_parts if part)
