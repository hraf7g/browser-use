from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.crawler.sources.bahrain_tender_board_crawler import (
	BahrainTenderBoardCrawlerError,
	BahrainTenderBoardCrawlResult,
	BahrainTenderBoardRawItem,
)
from src.crawler.sources.bahrain_tender_board_detail_crawler import (
	BahrainTenderBoardDetailCrawlResult,
	BahrainTenderBoardDetailItem,
)
from src.crawler.sources.bahrain_tender_board_enriched_normalizer import (
	normalize_bahrain_tender_board_enriched_item,
)
from src.crawler.sources.bahrain_tender_board_enriched_quality import (
	assess_bahrain_tender_board_enriched_payload,
)
from src.crawler.sources.bahrain_tender_board_run_service import (
	run_bahrain_tender_board_source,
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


def _build_source(name: str = 'Bahrain Tender Board') -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url='https://etendering.tenderboard.gov.bh',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def _build_dashboard_item() -> BahrainTenderBoardRawItem:
	return BahrainTenderBoardRawItem(
		item_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://etendering.tenderboard.gov.bh/Tenders/publicDash',
		title_text='Waterproofing and Roof Repairs Services',
		detail_url='https://etendering.tenderboard.gov.bh/Tenders/view/63',
		raw_text='63/2026/BTB (PHC/125/2025) Waterproofing and Roof Repairs Services',
		visible_tender_number='63/2026/BTB',
		visible_pa_reference='PHC/125/2025',
		visible_entity='Primary Health Care Centers',
		visible_time_left='15 Days -16 Hours',
	)


def _build_detail_item() -> BahrainTenderBoardDetailItem:
	dashboard_item = _build_dashboard_item()
	return BahrainTenderBoardDetailItem(
		item_index=dashboard_item.item_index,
		extracted_at=datetime.now(UTC),
		dashboard_title_text=dashboard_item.title_text,
		dashboard_visible_entity=dashboard_item.visible_entity,
		dashboard_visible_tender_number=dashboard_item.visible_tender_number,
		dashboard_visible_pa_reference=dashboard_item.visible_pa_reference,
		dashboard_visible_time_left=dashboard_item.visible_time_left,
		detail_url=dashboard_item.detail_url,
		final_url=dashboard_item.detail_url,
		detail_page_title='Tender Details',
		access_status='detail_page',
		detail_title='Waterproofing and Roof Repairs Services for Health Centers',
		detail_issuing_entity='Primary Health Care Centers',
		detail_tender_number='63/2026/BTB',
		detail_pa_reference='PHC/125/2025',
		detail_closing_date_raw='15-04-2026 08:30:00 AM',
		detail_published_at_raw='13-04-2026 11:46:23 AM',
		detail_opening_date_raw='16-04-2026 09:00:00 AM',
		detail_category='Public Tender',
		detail_document_indicators=('Tender Documents',),
		stronger_fields=('title', 'closing_date', 'publication_date', 'opening_date', 'category'),
		raw_text='Tender Details Closing Date 15-04-2026 08:30:00 AM',
	)


def test_bahrain_enriched_normalizer_parses_visible_detail_dates() -> None:
	source_id = uuid4()
	payload = normalize_bahrain_tender_board_enriched_item(
		source_id=source_id,
		item=_build_detail_item(),
	)

	assert payload.source_id == source_id
	assert payload.tender_ref == '63/2026/BTB'
	assert payload.category == 'Public Tender'
	assert payload.closing_date is not None
	assert payload.published_at is not None
	assert payload.opening_date is not None
	assert payload.closing_date.tzinfo == UTC


def test_bahrain_enriched_quality_accepts_strong_detail_payload() -> None:
	payload = normalize_bahrain_tender_board_enriched_item(
		source_id=uuid4(),
		item=_build_detail_item(),
	)

	assessment = assess_bahrain_tender_board_enriched_payload(payload)

	assert assessment.quality_score >= 70
	assert assessment.is_review_required is False
	assert 'closing_date_missing' not in assessment.quality_flags
	assert 'tender_ref_missing' not in assessment.quality_flags


def test_bahrain_run_service_success_persists_counts_and_source_health(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(
		execute_results=[_ScalarOneOrNoneResult(source)],
	)
	dashboard_item = _build_dashboard_item()
	detail_item = _build_detail_item()

	async def fake_run_bahrain_tender_board_crawl() -> BahrainTenderBoardCrawlResult:
		return BahrainTenderBoardCrawlResult(
			source_name='Bahrain Tender Board',
			listing_url='https://etendering.tenderboard.gov.bh/Tenders/publicDash',
			final_url='https://etendering.tenderboard.gov.bh/Tenders/publicDash',
			page_title='Welcome To Bahrain Tender Board',
			extracted_at=datetime.now(UTC),
			total_items=1,
			items=(dashboard_item,),
		)

	async def fake_run_bahrain_tender_board_detail_crawl(
		*,
		sample_size: int | None = 5,
		dashboard_items=None,
	) -> BahrainTenderBoardDetailCrawlResult:
		assert sample_size is None
		assert tuple(dashboard_items or ()) == (dashboard_item,)
		return BahrainTenderBoardDetailCrawlResult(
			source_name='Bahrain Tender Board',
			listing_url='https://etendering.tenderboard.gov.bh/Tenders/publicDash',
			final_listing_url='https://etendering.tenderboard.gov.bh/Tenders/publicDash',
			sample_count=1,
			successful_detail_pages=1,
			security_page_count=0,
			extracted_at=datetime.now(UTC),
			items=(detail_item,),
		)

	def fake_ingest_tender(*, session: object, payload: Any) -> tuple[object, bool]:
		return (
			SimpleNamespace(
				search_text='waterproofing primary health care public tender',
				source_id=source.id,
				title=payload.title,
			),
			True,
		)

	monkeypatch.setattr(
		'src.crawler.sources.bahrain_tender_board_run_service.run_bahrain_tender_board_crawl',
		fake_run_bahrain_tender_board_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.bahrain_tender_board_run_service.run_bahrain_tender_board_detail_crawl',
		fake_run_bahrain_tender_board_detail_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.bahrain_tender_board_run_service.ingest_tender',
		fake_ingest_tender,
	)

	result = run_bahrain_tender_board_source(session=cast(Session, session))

	assert result.status == 'success'
	assert result.crawled_row_count == 1
	assert result.detail_sampled_row_count == 1
	assert result.normalized_row_count == 1
	assert result.accepted_row_count == 1
	assert result.review_required_row_count == 0
	assert result.created_tender_count == 1
	assert result.updated_tender_count == 0
	assert source.status == 'healthy'
	assert source.failure_count == 0
	assert source.last_successful_run_at is not None
	assert any(getattr(item, 'status', None) == 'success' for item in session.added)


def test_bahrain_run_service_failure_marks_source_degraded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(
		execute_results=[_ScalarOneOrNoneResult(source)],
	)

	async def fake_run_bahrain_tender_board_crawl() -> BahrainTenderBoardCrawlResult:
		raise BahrainTenderBoardCrawlerError('blocked by source')

	monkeypatch.setattr(
		'src.crawler.sources.bahrain_tender_board_run_service.run_bahrain_tender_board_crawl',
		fake_run_bahrain_tender_board_crawl,
	)

	result = run_bahrain_tender_board_source(session=cast(Session, session))

	assert result.status == 'failed'
	assert result.failure_step == 'crawl'
	assert result.failure_reason == 'blocked by source'
	assert source.status == 'degraded'
	assert source.failure_count == 1
	assert source.last_failed_run_at is not None
	assert any(getattr(item, 'status', None) == 'failed' for item in session.added)
