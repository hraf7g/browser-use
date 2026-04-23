from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.crawler.sources.saudi_misa_crawler import (
	SaudiMisaCrawlerError,
	SaudiMisaCrawlResult,
	SaudiMisaRawItem,
)
from src.crawler.sources.saudi_misa_detail_crawler import (
	SaudiMisaDetailCrawlResult,
	SaudiMisaDetailItem,
)
from src.crawler.sources.saudi_misa_enriched_normalizer import (
	normalize_saudi_misa_enriched_item,
)
from src.crawler.sources.saudi_misa_enriched_quality import (
	assess_saudi_misa_enriched_payload,
)
from src.crawler.sources.saudi_misa_run_service import run_saudi_misa_source
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


def _build_source(name: str = 'Saudi MISA Procurements') -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url='https://misa.gov.sa',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def _build_dashboard_item() -> SaudiMisaRawItem:
	return SaudiMisaRawItem(
		item_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://misa.gov.sa/ar/resources/procurements/',
		title_text='استدامة الأعمال والتحديث لحصر وجرد الأصول',
		detail_url='https://tenders.etimad.sa/Tender/OpenTenderDetailsReportForVisitor?tenderIdString=y0HAFQXho23d%2A%40%40%2A%2AnM1NVFzsA%3D%3D',
		raw_text='استدامة الأعمال والتحديث لحصر وجرد الأصول 26/22 03/04/2026 08/04/2026',
		visible_reference_number='26/22',
		visible_offering_date='03/04/2026',
		visible_inquiry_deadline='05/04/2026',
		visible_bid_deadline='08/04/2026',
		visible_status_link_text='عرض',
	)


def _build_detail_item() -> SaudiMisaDetailItem:
	dashboard_item = _build_dashboard_item()
	return SaudiMisaDetailItem(
		item_index=dashboard_item.item_index,
		extracted_at=datetime.now(UTC),
		table_title_text=dashboard_item.title_text,
		table_reference_number=dashboard_item.visible_reference_number,
		table_inquiry_deadline_primary=dashboard_item.visible_offering_date,
		table_inquiry_deadline_secondary=dashboard_item.visible_bid_deadline,
		table_offer_opening_primary=dashboard_item.visible_inquiry_deadline,
		table_offer_opening_secondary=dashboard_item.visible_bid_deadline,
		table_status_link_text=dashboard_item.visible_status_link_text,
		detail_url=dashboard_item.detail_url,
		final_url=dashboard_item.detail_url,
		detail_page_title='تفاصيل المنافسة',
		access_status='detail_page',
		detail_title='استدامة الأعمال والتحديث لحصر وجرد الأصول',
		detail_issuing_entity='معهد الادارة العامة',
		detail_tender_ref='26/22',
		detail_closing_date_raw='08/04/2026',
		detail_published_at_raw='03/04/2026',
		detail_opening_date_raw='08/04/2026',
		detail_category='تقنية المعلومات / الأصول',
		detail_procurement_type=None,
		detail_description='حصر وجرد اصول معهد الادارة العامة',
		detail_document_indicators=('تحميل',),
		detail_public_action_indicators=('عرض',),
		stronger_fields=('issuing_entity', 'opening_or_published_date', 'category_or_procurement_type'),
		raw_text='تفاصيل المنافسة الجهة الحكومية معهد الادارة العامة رقم المنافسة 26/22',
	)


def test_saudi_misa_enriched_normalizer_prefers_detail_fields() -> None:
	source_id = uuid4()
	payload = normalize_saudi_misa_enriched_item(
		source_id=source_id,
		item=_build_detail_item(),
	)

	assert payload.source_id == source_id
	assert payload.issuing_entity == 'معهد الادارة العامة'
	assert payload.tender_ref == '26/22'
	assert payload.category == 'تقنية المعلومات / الأصول'
	assert payload.published_at is not None
	assert payload.closing_date is not None
	assert payload.opening_date is not None
	assert payload.closing_date.tzinfo == UTC


def test_saudi_misa_enriched_quality_accepts_strong_payload() -> None:
	payload = normalize_saudi_misa_enriched_item(
		source_id=uuid4(),
		item=_build_detail_item(),
	)

	assessment = assess_saudi_misa_enriched_payload(payload)

	assert assessment.quality_score >= 70
	assert assessment.is_review_required is False
	assert 'closing_date_missing' not in assessment.quality_flags
	assert 'category_missing' not in assessment.quality_flags


def test_saudi_misa_run_service_success_persists_counts_and_source_health(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])
	dashboard_item = _build_dashboard_item()
	detail_item = _build_detail_item()

	async def fake_run_saudi_misa_crawl() -> SaudiMisaCrawlResult:
		return SaudiMisaCrawlResult(
			source_name='Saudi MISA Procurements',
			listing_url='https://misa.gov.sa/ar/resources/procurements/',
			final_url='https://misa.gov.sa/ar/resources/procurements/',
			page_title='المشتريات',
			extracted_at=datetime.now(UTC),
			total_items=1,
			items=(dashboard_item,),
		)

	async def fake_run_saudi_misa_detail_crawl(
		*,
		sample_size: int | None = 5,
		dashboard_items=None,
	) -> SaudiMisaDetailCrawlResult:
		assert sample_size is None
		assert tuple(dashboard_items or ()) == (dashboard_item,)
		return SaudiMisaDetailCrawlResult(
			source_name='Saudi MISA Procurements',
			listing_url='https://misa.gov.sa/ar/resources/procurements/',
			final_listing_url='https://misa.gov.sa/ar/resources/procurements/',
			sample_count=1,
			successful_detail_pages=1,
			blocked_page_count=0,
			enrichment_supported=True,
			extracted_at=datetime.now(UTC),
			items=(detail_item,),
		)

	def fake_ingest_tender(*, session: object, payload: Any) -> tuple[object, bool]:
		return (
			SimpleNamespace(
				search_text='misa asset inventory tender institute of public administration',
				source_id=source.id,
				title=payload.title,
			),
			True,
		)

	monkeypatch.setattr(
		'src.crawler.sources.saudi_misa_run_service.run_saudi_misa_crawl',
		fake_run_saudi_misa_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.saudi_misa_run_service.run_saudi_misa_detail_crawl',
		fake_run_saudi_misa_detail_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.saudi_misa_run_service.ingest_tender',
		fake_ingest_tender,
	)

	result = run_saudi_misa_source(session=cast(Session, session))

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


def test_saudi_misa_run_service_failure_marks_source_degraded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])

	async def fake_run_saudi_misa_crawl() -> SaudiMisaCrawlResult:
		raise SaudiMisaCrawlerError('blocked by source')

	monkeypatch.setattr(
		'src.crawler.sources.saudi_misa_run_service.run_saudi_misa_crawl',
		fake_run_saudi_misa_crawl,
	)

	result = run_saudi_misa_source(session=cast(Session, session))

	assert result.status == 'failed'
	assert result.failure_step == 'crawl'
	assert result.failure_reason == 'blocked by source'
	assert source.status == 'degraded'
	assert source.failure_count == 1
	assert source.last_failed_run_at is not None
	assert any(getattr(item, 'status', None) == 'failed' for item in session.added)
