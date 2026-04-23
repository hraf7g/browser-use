from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import cast

from sqlalchemy.orm import Session

from src.ingestion.tender_ingestion_service import ingest_tender
from src.shared.industry_taxonomy import classify_industry_codes
from src.shared.schemas.tender_ingestion import TenderIngestionInput


class _FakeScalarResult:
	def scalar_one_or_none(self):
		return None


class _FakeSession:
	def __init__(self) -> None:
		self.added: list[object] = []

	def execute(self, _query):
		return _FakeScalarResult()

	def add(self, item: object) -> None:
		self.added.append(item)

	def flush(self) -> None:
		return None


def test_classify_industry_codes_maps_category_and_summary_into_canonical_codes() -> None:
	industry_codes = classify_industry_codes(
		category='Information Technology and Cybersecurity',
		title='Network security upgrade project',
		issuing_entity='Ministry of Digital Government',
		ai_summary='Procurement includes software, hardware, and security operations support.',
	)

	assert industry_codes == ['technology', 'security']


def test_ingest_tender_persists_classified_industry_codes_when_payload_omits_them() -> None:
	session = _FakeSession()

	tender, created = ingest_tender(
		session=cast(Session, session),
		payload=TenderIngestionInput(
			source_id=uuid.uuid4(),
			source_url='https://example.com/tenders/1',
			title='Hospital equipment and medical systems supply',
			issuing_entity='Health Authority',
			closing_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
			dedupe_key='tender-1',
			category='Medical Equipment',
			ai_summary='Healthcare devices and related installation services.',
		),
	)

	assert created is True
	assert tender.industry_codes == ['healthcare']
	assert tender.primary_industry_code == 'healthcare'
