from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.crawler.sources.dubai_esupply_crawler import (
	DubaiESupplyCrawlerError,
	DubaiESupplyCrawlResult,
	DubaiESupplyListingRow,
)
from src.crawler.sources.dubai_esupply_normalizer import normalize_dubai_esupply_row
from src.crawler.sources.dubai_esupply_quality import assess_dubai_esupply_payload
from src.crawler.sources.dubai_esupply_run_service import run_dubai_esupply_source
from src.db.models.source import Source


class _FakeQuery:
	def __init__(self, value: object | None):
		self._value = value

	def filter(self, *_args: object, **_kwargs: object) -> _FakeQuery:
		return self

	def one_or_none(self) -> object | None:
		return self._value


class _FakeNestedTransaction:
	def __enter__(self) -> _FakeNestedTransaction:
		return self

	def __exit__(self, exc_type, exc, tb) -> bool:
		return False


class FakeSession:
	def __init__(self, *, source: Source):
		self._source = source
		self.added: list[object] = []
		self.flush_calls = 0

	def query(self, _model: object) -> _FakeQuery:
		return _FakeQuery(self._source)

	def add(self, value: object) -> None:
		self.added.append(value)

	def flush(self) -> None:
		self.flush_calls += 1
		for value in self.added:
			if getattr(value, 'id', None) is None:
				setattr(value, 'id', uuid4())

	def begin_nested(self) -> _FakeNestedTransaction:
		return _FakeNestedTransaction()


def _build_source(name: str = 'Dubai eSupply') -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url='https://esupply.dubai.gov.ae',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def _build_row() -> DubaiESupplyListingRow:
	return DubaiESupplyListingRow(
		row_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://esupply.dubai.gov.ae/esop/guest/go/public/opportunity/current?_ncp=123',
		action_href='https://esupply.dubai.gov.ae/esop/guest/go/opportunity/detail?opportunityId=12607620&_ncp=456',
		cells=(
			'AED',
			'Roads and Transport Authority',
			'12607620-IVECO TRUCK',
			'21/04/2026 14:30',
			'Transport',
			'View',
		),
		row_text='AED Roads and Transport Authority 12607620-IVECO TRUCK 21/04/2026 14:30 Transport View',
	)


def test_dubai_esupply_normalizer_prefers_row_action_href() -> None:
	payload = normalize_dubai_esupply_row(source_id=uuid4(), row=_build_row())

	assert payload.source_url.startswith('https://esupply.dubai.gov.ae/esop/guest/go/opportunity/detail')
	assert '_ncp=' not in payload.source_url
	assert payload.tender_ref == '12607620'
	assert payload.title == 'IVECO TRUCK'
	assert payload.issuing_entity == 'Roads and Transport Authority'
	assert payload.closing_date is not None


def test_dubai_esupply_quality_accepts_strong_payload() -> None:
	payload = normalize_dubai_esupply_row(source_id=uuid4(), row=_build_row())
	assessment = assess_dubai_esupply_payload(payload)

	assert assessment.quality_score >= 70
	assert assessment.is_review_required is False
	assert 'tender_ref_missing' not in assessment.quality_flags


def test_dubai_esupply_run_service_success_persists_counts_and_source_health(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(source=source)
	row = _build_row()

	async def fake_run_dubai_esupply_crawl() -> DubaiESupplyCrawlResult:
		return DubaiESupplyCrawlResult(
			source_name='Dubai eSupply',
			listing_url='https://esupply.dubai.gov.ae/esop/guest/go/public/opportunity/current',
			page_title='Current Opportunities',
			extracted_at=datetime.now(UTC),
			total_rows=1,
			rows=(row,),
		)

	def fake_ingest_tender(*, session: object, payload: Any) -> tuple[object, bool]:
		return (
			SimpleNamespace(
				search_text='iveco truck roads and transport authority transport',
				source_id=source.id,
				title=payload.title,
			),
			True,
		)

	monkeypatch.setattr(
		'src.crawler.sources.dubai_esupply_run_service.run_dubai_esupply_crawl',
		fake_run_dubai_esupply_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.dubai_esupply_run_service.ingest_tender',
		fake_ingest_tender,
	)

	result = run_dubai_esupply_source(session=cast(Session, session))

	assert result.status == 'success'
	assert result.crawled_row_count == 1
	assert result.normalized_row_count == 1
	assert result.accepted_row_count == 1
	assert result.review_required_row_count == 0
	assert result.created_tender_count == 1
	assert result.updated_tender_count == 0
	assert source.status == 'healthy'
	assert source.failure_count == 0
	assert source.last_successful_run_at is not None
	assert any(getattr(item, 'status', None) == 'success' for item in session.added)


def test_dubai_esupply_run_service_failure_marks_source_degraded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(source=source)

	async def fake_run_dubai_esupply_crawl() -> DubaiESupplyCrawlResult:
		raise DubaiESupplyCrawlerError('blocked by source')

	monkeypatch.setattr(
		'src.crawler.sources.dubai_esupply_run_service.run_dubai_esupply_crawl',
		fake_run_dubai_esupply_crawl,
	)

	result = run_dubai_esupply_source(session=cast(Session, session))

	assert result.status == 'failed'
	assert result.failure_step == 'crawl'
	assert result.failure_reason == 'blocked by source'
	assert source.status == 'degraded'
	assert source.failure_count == 1
	assert source.last_failed_run_at is not None
	assert any(getattr(item, 'status', None) == 'failed' for item in session.added)
