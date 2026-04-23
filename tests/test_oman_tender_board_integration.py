from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.crawler.sources.oman_tender_board_crawler import (
	OmanTenderBoardCrawlerError,
	OmanTenderBoardCrawlResult,
	OmanTenderBoardRawItem,
)
from src.crawler.sources.oman_tender_board_normalizer import (
	normalize_oman_tender_board_item,
)
from src.crawler.sources.oman_tender_board_quality import (
	assess_oman_tender_board_payload,
)
from src.crawler.sources.oman_tender_board_run_service import (
	run_oman_tender_board_source,
)
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


def _build_source(name: str = 'Oman Tender Board') -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url='https://etendering.tenderboard.gov.om',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def _build_item() -> OmanTenderBoardRawItem:
	return OmanTenderBoardRawItem(
		item_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://etendering.tenderboard.gov.om/product/publicDash?viewFlag=NewTenders',
		title_text='Supply, Installation and Maintenance of Smart Monitoring System',
		detail_url='https://etendering.tenderboard.gov.om/product/publicDash?nitNo=154321',
		raw_text='154321 Supply, Installation and Maintenance of Smart Monitoring System',
		visible_tender_number='154321',
		visible_entity='Ministry of Transport, Communications and Information Technology',
		visible_procurement_category=None,
		visible_tender_type='International Tender',
		visible_sales_end_date='20-04-2026',
		visible_bid_closing_date='23-04-2026',
	)


def test_oman_normalizer_falls_back_to_tender_type_for_category() -> None:
	payload = normalize_oman_tender_board_item(source_id=uuid4(), item=_build_item())

	assert payload.tender_ref == '154321'
	assert payload.category == 'International Tender'
	assert payload.published_at is None
	assert payload.closing_date is not None


def test_oman_quality_does_not_flag_missing_published_at() -> None:
	payload = normalize_oman_tender_board_item(source_id=uuid4(), item=_build_item())
	assessment = assess_oman_tender_board_payload(payload)

	assert 'published_at_missing' not in assessment.quality_flags
	assert assessment.quality_score >= 70
	assert assessment.is_review_required is False


def test_oman_run_service_success_persists_counts_and_source_health(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])
	item = _build_item()

	async def fake_run_oman_tender_board_crawl() -> OmanTenderBoardCrawlResult:
		return OmanTenderBoardCrawlResult(
			source_name='Oman Tender Board',
			listing_url='https://etendering.tenderboard.gov.om/product/publicDash?viewFlag=NewTenders',
			final_url='https://etendering.tenderboard.gov.om/product/publicDash?viewFlag=NewTenders',
			page_title='Welcome To Oman Tender Board',
			extracted_at=datetime.now(UTC),
			total_items=1,
			items=(item,),
		)

	def fake_ingest_tender(*, session: object, payload: Any) -> tuple[object, bool]:
		return (
			SimpleNamespace(
				search_text='smart monitoring system ministry of transport international tender',
				source_id=source.id,
				title=payload.title,
			),
			True,
		)

	monkeypatch.setattr(
		'src.crawler.sources.oman_tender_board_run_service.run_oman_tender_board_crawl',
		fake_run_oman_tender_board_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.oman_tender_board_run_service.ingest_tender',
		fake_ingest_tender,
	)

	result = run_oman_tender_board_source(session=cast(Session, session))

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


def test_oman_run_service_failure_marks_source_degraded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])

	async def fake_run_oman_tender_board_crawl() -> OmanTenderBoardCrawlResult:
		raise OmanTenderBoardCrawlerError('blocked by source')

	monkeypatch.setattr(
		'src.crawler.sources.oman_tender_board_run_service.run_oman_tender_board_crawl',
		fake_run_oman_tender_board_crawl,
	)

	result = run_oman_tender_board_source(session=cast(Session, session))

	assert result.status == 'failed'
	assert result.failure_step == 'crawl'
	assert result.failure_reason == 'blocked by source'
	assert source.status == 'degraded'
	assert source.failure_count == 1
	assert source.last_failed_run_at is not None
	assert any(getattr(item, 'status', None) == 'failed' for item in session.added)
