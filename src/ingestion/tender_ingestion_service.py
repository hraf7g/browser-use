from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.tender import Tender
from src.ingestion.tender_derived_fields import (
	build_primary_industry_code,
	build_tender_industry_codes,
	build_tender_search_text,
)
from src.shared.schemas.tender_ingestion import TenderIngestionInput


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
	existing_by_dedupe = session.execute(
		select(Tender).where(
			Tender.source_id == payload.source_id,
			Tender.dedupe_key == payload.dedupe_key,
		)
	).scalar_one_or_none()
	existing_by_ref = None
	if payload.tender_ref is not None:
		existing_by_ref = session.execute(
			select(Tender).where(
				Tender.source_id == payload.source_id,
				Tender.tender_ref == payload.tender_ref,
			)
		).scalar_one_or_none()

	if existing_by_dedupe is not None and existing_by_ref is not None and existing_by_dedupe.id != existing_by_ref.id:
		raise ValueError(
			'conflicting tender identities detected for the same source: '
			'dedupe_key matched one row while tender_ref matched another'
		)

	existing_tender = existing_by_dedupe if existing_by_dedupe is not None else existing_by_ref

	industry_codes = build_tender_industry_codes(
		category=payload.category,
		title=payload.title,
		issuing_entity=payload.issuing_entity,
		ai_summary=payload.ai_summary,
		explicit_industry_codes=payload.industry_codes,
	)
	primary_industry_code = build_primary_industry_code(industry_codes)
	search_text = build_tender_search_text(
		title=payload.title,
		issuing_entity=payload.issuing_entity,
		category=payload.category,
		ai_summary=payload.ai_summary,
		tender_ref=payload.tender_ref,
	)

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
			industry_codes=list(industry_codes),
			primary_industry_code=primary_industry_code,
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
	existing_tender.industry_codes = list(industry_codes)
	existing_tender.primary_industry_code = primary_industry_code
	existing_tender.ai_summary = payload.ai_summary
	existing_tender.search_text = search_text

	session.flush()
	return existing_tender, False
