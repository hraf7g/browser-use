from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.crawler.sources.saudi_etimad_crawler import (
	SaudiEtimadCrawlerError,
	SaudiEtimadCrawlResult,
	SaudiEtimadRawItem,
)
from src.crawler.sources.saudi_etimad_detail_crawler import (
	SaudiEtimadDetailCrawlResult,
	SaudiEtimadDetailItem,
)
from src.crawler.sources.saudi_etimad_enriched_normalizer import (
	normalize_saudi_etimad_enriched_item,
)
from src.crawler.sources.saudi_etimad_enriched_quality import (
	assess_saudi_etimad_enriched_payload,
)
from src.crawler.sources.saudi_etimad_run_service import run_saudi_etimad_source
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


def _build_source(name: str = 'Saudi Etimad') -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url='https://tenders.etimad.sa',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def _build_dashboard_item() -> SaudiEtimadRawItem:
	return SaudiEtimadRawItem(
		item_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://tenders.etimad.sa/Tender/',
		title_text='توريد وتركيب نظام الملف الطبي الإلكتروني',
		issuing_entity=None,
		publication_date='2026-04-01',
		procurement_type_label='منافسة عامة',
		visible_reference='251139008726',
		visible_closing_date_raw='19/04/2026 14:00',
		visible_opening_date_raw='20/04/2026 09:00',
		detail_url='https://tenders.etimad.sa/Tender/DetailsForVisitor?STenderId=y8DGd16OPiV29fISdHLrEA%3D%3D',
		raw_text='تاريخ النشر : 2026-04-01 منافسة عامة توريد وتركيب نظام الملف الطبي الإلكتروني',
		reference_fields=('الرقم المرجعي 251139008726',),
		date_fields=(
			'آخر موعد لتقديم العروض 19/04/2026 14:00',
			'تاريخ ووقت فتح العروض 20/04/2026 09:00',
		),
	)


def _build_detail_item() -> SaudiEtimadDetailItem:
	dashboard_item = _build_dashboard_item()
	return SaudiEtimadDetailItem(
		item_index=dashboard_item.item_index,
		extracted_at=datetime.now(UTC),
		dashboard_title_text=dashboard_item.title_text,
		dashboard_issuing_entity=dashboard_item.issuing_entity,
		dashboard_publication_date=dashboard_item.publication_date,
		dashboard_procurement_type_label=dashboard_item.procurement_type_label,
		dashboard_visible_reference=dashboard_item.visible_reference,
		dashboard_visible_closing_date_raw=dashboard_item.visible_closing_date_raw,
		dashboard_visible_opening_date_raw=dashboard_item.visible_opening_date_raw,
		detail_url=dashboard_item.detail_url,
		final_url=dashboard_item.detail_url,
		detail_page_title='تفاصيل المنافسة',
		access_status='detail_page',
		detail_title='توريد وتركيب نظام الملف الطبي الإلكتروني',
		detail_issuing_entity='الجامعة السعودية الالكترونية',
		detail_competition_number='28/2025',
		detail_reference_number='251139008726',
		detail_procurement_type='منافسة عامة',
		detail_remaining_time_raw='إنتهى',
		stronger_fields=('issuing_entity', 'tender_ref'),
		raw_text='تفاصيل المنافسة الجهة الحكوميه الجامعة السعودية الالكترونية رقم المنافسة 28/2025',
	)


def test_saudi_etimad_enriched_normalizer_parses_visible_listing_dates() -> None:
	source_id = uuid4()
	payload = normalize_saudi_etimad_enriched_item(
		source_id=source_id,
		item=_build_detail_item(),
	)

	assert payload.source_id == source_id
	assert payload.issuing_entity == 'الجامعة السعودية الالكترونية'
	assert payload.tender_ref == '28/2025'
	assert payload.category == 'منافسة عامة'
	assert payload.published_at is not None
	assert payload.closing_date is not None
	assert payload.opening_date is not None
	assert payload.closing_date != payload.published_at
	assert payload.closing_date.tzinfo == UTC


def test_saudi_etimad_enriched_quality_accepts_strong_payload() -> None:
	payload = normalize_saudi_etimad_enriched_item(
		source_id=uuid4(),
		item=_build_detail_item(),
	)

	assessment = assess_saudi_etimad_enriched_payload(payload)

	assert assessment.quality_score >= 70
	assert assessment.is_review_required is False
	assert 'closing_date_missing' not in assessment.quality_flags
	assert 'issuing_entity_platform_fallback' not in assessment.quality_flags


def test_saudi_etimad_run_service_success_persists_counts_and_source_health(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])
	dashboard_item = _build_dashboard_item()
	detail_item = _build_detail_item()

	async def fake_run_saudi_etimad_crawl() -> SaudiEtimadCrawlResult:
		return SaudiEtimadCrawlResult(
			source_name='Saudi Etimad',
			listing_url='https://tenders.etimad.sa/Tender/',
			final_url='https://tenders.etimad.sa/Tender/',
			page_title='المنافسات',
			extracted_at=datetime.now(UTC),
			total_items=1,
			items=(dashboard_item,),
		)

	async def fake_run_saudi_etimad_detail_crawl(
		*,
		sample_size: int | None = 5,
		dashboard_items=None,
	) -> SaudiEtimadDetailCrawlResult:
		assert sample_size is None
		assert tuple(dashboard_items or ()) == (dashboard_item,)
		return SaudiEtimadDetailCrawlResult(
			source_name='Saudi Etimad',
			listing_url='https://tenders.etimad.sa/Tender/',
			final_listing_url='https://tenders.etimad.sa/Tender/',
			sample_count=1,
			successful_detail_pages=1,
			extracted_at=datetime.now(UTC),
			items=(detail_item,),
		)

	def fake_ingest_tender(*, session: object, payload: Any) -> tuple[object, bool]:
		return (
			SimpleNamespace(
				search_text='saudi etimad medical record system public tender saudi electronic university',
				source_id=source.id,
				title=payload.title,
			),
			True,
		)

	monkeypatch.setattr(
		'src.crawler.sources.saudi_etimad_run_service.run_saudi_etimad_crawl',
		fake_run_saudi_etimad_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.saudi_etimad_run_service.run_saudi_etimad_detail_crawl',
		fake_run_saudi_etimad_detail_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.saudi_etimad_run_service.ingest_tender',
		fake_ingest_tender,
	)

	result = run_saudi_etimad_source(session=cast(Session, session))

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


def test_saudi_etimad_run_service_failure_marks_source_degraded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])

	async def fake_run_saudi_etimad_crawl() -> SaudiEtimadCrawlResult:
		raise SaudiEtimadCrawlerError('blocked by source')

	monkeypatch.setattr(
		'src.crawler.sources.saudi_etimad_run_service.run_saudi_etimad_crawl',
		fake_run_saudi_etimad_crawl,
	)

	result = run_saudi_etimad_source(session=cast(Session, session))

	assert result.status == 'failed'
	assert result.failure_step == 'crawl'
	assert result.failure_reason == 'blocked by source'
	assert source.status == 'degraded'
	assert source.failure_count == 1
	assert source.last_failed_run_at is not None
	assert any(getattr(item, 'status', None) == 'failed' for item in session.added)
