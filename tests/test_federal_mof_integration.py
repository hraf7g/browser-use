from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.crawler.sources.federal_mof_crawler import (
	FederalMOFCrawlerError,
	FederalMOFCrawlResult,
	FederalMOFLinkItem,
	FederalMOFTableRow,
)
from src.crawler.sources.federal_mof_normalizer import normalize_federal_mof_row
from src.crawler.sources.federal_mof_quality import assess_federal_mof_quality
from src.crawler.sources.federal_mof_run_service import run_federal_mof_source
from src.db.models.source import Source


class _ScalarOneOrNoneResult:
	def __init__(self, value: object | None):
		self._value = value

	def scalar_one_or_none(self) -> object | None:
		return self._value


class _FakeNestedTransaction:
	def __enter__(self) -> _FakeNestedTransaction:
		return self

	def __exit__(self, exc_type, exc, tb) -> bool:
		return False


class FakeSession:
	def __init__(self, *, execute_results: list[object]):
		self._execute_results = list(execute_results)
		self.added: list[object] = []
		self.flush_calls = 0

	def execute(self, statement: object) -> object:
		if not self._execute_results:
			raise AssertionError('unexpected execute() call')
		return self._execute_results.pop(0)

	def add(self, value: object) -> None:
		self.added.append(value)

	def flush(self) -> None:
		self.flush_calls += 1
		for value in self.added:
			if getattr(value, 'id', None) is None:
				setattr(value, 'id', uuid4())

	def begin_nested(self) -> _FakeNestedTransaction:
		return _FakeNestedTransaction()


def _build_source(name: str = 'Federal MOF') -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url='https://mof.gov.ae',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def _build_table_row() -> FederalMOFTableRow:
	return FederalMOFTableRow(
		row_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://mof.gov.ae/tenders-and-auctions/',
		action_href='https://procurement.gov.ae/tender/10543',
		cells=(
			'10543',
			'Ministry of Education - (109/16894)',
			'English Levelled Reading Resources and Programme',
			'23/03/2026 10:14:34 AM',
			'13/05/2026 3:00:00 PM',
			'Click here',
		),
		row_text='10543 Ministry of Education English Levelled Reading Resources and Programme',
	)


def test_federal_mof_normalizer_prefers_row_action_href() -> None:
	source_id = uuid4()
	payload = normalize_federal_mof_row(source_id=source_id, row=_build_table_row())

	assert payload.source_id == source_id
	assert payload.source_url == 'https://procurement.gov.ae/tender/10543'
	assert payload.tender_ref == '10543'
	assert payload.issuing_entity == 'Ministry of Education - (109/16894)'
	assert payload.published_at is not None
	assert payload.closing_date is not None
	assert payload.opening_date == payload.published_at


def test_federal_mof_quality_flags_platform_fallback_entity() -> None:
	row = FederalMOFTableRow(
		row_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://mof.gov.ae/tenders-and-auctions/',
		action_href=None,
		cells=(
			'10543',
			'English Levelled Reading Resources and Programme',
			'23/03/2026 10:14:34 AM',
			'13/05/2026 3:00:00 PM',
			'Click here',
		),
		row_text='10543 English Levelled Reading Resources and Programme',
	)

	payload = normalize_federal_mof_row(source_id=uuid4(), row=row)
	assessment = assess_federal_mof_quality(payload)

	assert 'issuing_entity_platform_fallback' in assessment.quality_flags
	assert assessment.is_review_required is True


def test_federal_mof_run_service_success_persists_counts_and_source_health(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])
	row = _build_table_row()

	async def fake_run_federal_mof_crawl() -> FederalMOFCrawlResult:
		return FederalMOFCrawlResult(
			source_name='Federal MOF',
			listing_url='https://mof.gov.ae/tenders-and-auctions/',
			page_title='Current Business Opportunities',
			extracted_at=datetime.now(UTC),
			total_links=1,
			total_table_rows=1,
			links=(
				FederalMOFLinkItem(
					item_index=0,
					extracted_at=datetime.now(UTC),
					page_url='https://mof.gov.ae/tenders-and-auctions/',
					link_text='Click here',
					href=row.action_href,
				),
			),
			table_rows=(row,),
		)

	def fake_ingest_tender(*, session: object, payload: Any) -> tuple[object, bool]:
		return (
			SimpleNamespace(
				search_text='english levelled reading resources ministry of education',
				source_id=source.id,
				title=payload.title,
			),
			True,
		)

	monkeypatch.setattr(
		'src.crawler.sources.federal_mof_run_service.run_federal_mof_crawl',
		fake_run_federal_mof_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.federal_mof_run_service.ingest_tender',
		fake_ingest_tender,
	)

	result = run_federal_mof_source(session=cast(Session, session))

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


def test_federal_mof_run_service_failure_marks_source_degraded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])

	async def fake_run_federal_mof_crawl() -> FederalMOFCrawlResult:
		raise FederalMOFCrawlerError('blocked by source')

	monkeypatch.setattr(
		'src.crawler.sources.federal_mof_run_service.run_federal_mof_crawl',
		fake_run_federal_mof_crawl,
	)

	result = run_federal_mof_source(session=cast(Session, session))

	assert result.status == 'failed'
	assert result.failure_step == 'crawl'
	assert result.failure_reason == 'blocked by source'
	assert source.status == 'degraded'
	assert source.failure_count == 1
	assert source.last_failed_run_at is not None
	assert any(getattr(item, 'status', None) == 'failed' for item in session.added)
