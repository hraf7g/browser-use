from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.crawler.sources.abu_dhabi_gpg_crawler import (
	AbuDhabiGPGCrawlerError,
	AbuDhabiGPGCrawlResult,
	AbuDhabiGPGRawItem,
)
from src.crawler.sources.abu_dhabi_gpg_detail_crawler import (
	AbuDhabiGPGDetailCrawlResult,
	AbuDhabiGPGDetailItem,
)
from src.crawler.sources.abu_dhabi_gpg_enriched_normalizer import (
	normalize_abu_dhabi_gpg_enriched_item,
)
from src.crawler.sources.abu_dhabi_gpg_enriched_quality import (
	assess_abu_dhabi_gpg_enriched_payload,
)
from src.crawler.sources.abu_dhabi_gpg_run_service import run_abu_dhabi_gpg_source
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


def _build_source(name: str = 'Abu Dhabi GPG') -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url='https://adgpg.gov.ae',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def _build_widget_item() -> AbuDhabiGPGRawItem:
	return AbuDhabiGPGRawItem(
		item_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://adgpg.gov.ae',
		title_text='Road Safety Monitoring Platform',
		detail_url='https://adgpg.gov.ae/tenders/road-safety-monitoring-platform',
		raw_text='Road Safety Monitoring Platform',
		visible_due_date='21 Apr 2026',
		visible_category_label='Information Technology',
		visible_notice_type='RFP',
		visible_short_description='Digital monitoring platform for road safety compliance.',
	)


def _build_detail_item() -> AbuDhabiGPGDetailItem:
	widget_item = _build_widget_item()
	return AbuDhabiGPGDetailItem(
		item_index=widget_item.item_index,
		extracted_at=datetime.now(UTC),
		widget_title_text=widget_item.title_text,
		widget_visible_due_date=widget_item.visible_due_date,
		widget_visible_category_label=widget_item.visible_category_label,
		widget_visible_notice_type=widget_item.visible_notice_type,
		widget_visible_short_description=widget_item.visible_short_description,
		detail_url=widget_item.detail_url,
		final_url=widget_item.detail_url,
		detail_page_title='Road Safety Monitoring Platform',
		access_status='detail_page',
		detail_title='Road Safety Monitoring Platform',
		detail_issuing_entity='Integrated Transport Centre',
		detail_tender_ref='ITC-2026-042',
		detail_closing_date_raw='21 Apr 2026',
		detail_published_at_raw=None,
		detail_opening_date_raw='22 Apr 2026',
		detail_category='Information Technology',
		detail_notice_type='RFP',
		detail_description='Digital monitoring platform for road safety compliance.',
		detail_document_indicators=('download',),
		detail_public_action_indicators=('participate now',),
		stronger_fields=('issuing_entity', 'tender_ref', 'opening_date'),
		raw_text='Road Safety Monitoring Platform Integrated Transport Centre 21 Apr 2026',
	)


def test_abu_dhabi_gpg_enriched_normalizer_keeps_missing_published_at_none() -> None:
	payload = normalize_abu_dhabi_gpg_enriched_item(
		source_id=uuid4(),
		item=_build_detail_item(),
	)

	assert payload.issuing_entity == 'Integrated Transport Centre'
	assert payload.tender_ref == 'ITC-2026-042'
	assert payload.category == 'Information Technology'
	assert payload.published_at is None
	assert payload.closing_date is not None
	assert payload.opening_date is not None


def test_abu_dhabi_gpg_enriched_quality_does_not_flag_missing_published_at() -> None:
	payload = normalize_abu_dhabi_gpg_enriched_item(
		source_id=uuid4(),
		item=_build_detail_item(),
	)
	assessment = assess_abu_dhabi_gpg_enriched_payload(payload)

	assert 'published_at_missing' not in assessment.quality_flags
	assert assessment.quality_score >= 70
	assert assessment.is_review_required is False


def test_abu_dhabi_gpg_run_service_success_persists_counts_and_source_health(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])
	widget_item = _build_widget_item()
	detail_item = _build_detail_item()

	async def fake_run_abu_dhabi_gpg_crawl() -> AbuDhabiGPGCrawlResult:
		return AbuDhabiGPGCrawlResult(
			source_name='Abu Dhabi GPG',
			listing_url='https://adgpg.gov.ae',
			final_url='https://adgpg.gov.ae',
			page_title='Abu Dhabi Government Procurement Gateway',
			extracted_at=datetime.now(UTC),
			total_items=1,
			items=(widget_item,),
		)

	async def fake_run_abu_dhabi_gpg_detail_crawl(
		*,
		sample_size: int | None = 5,
		widget_items=None,
		jitter_range_ms=None,
	) -> AbuDhabiGPGDetailCrawlResult:
		assert sample_size is None
		assert tuple(widget_items or ()) == (widget_item,)
		return AbuDhabiGPGDetailCrawlResult(
			source_name='Abu Dhabi GPG',
			listing_url='https://adgpg.gov.ae',
			final_listing_url='https://adgpg.gov.ae',
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
				search_text='road safety monitoring platform integrated transport centre',
				source_id=source.id,
				title=payload.title,
			),
			True,
		)

	monkeypatch.setattr(
		'src.crawler.sources.abu_dhabi_gpg_run_service.run_abu_dhabi_gpg_crawl',
		fake_run_abu_dhabi_gpg_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.abu_dhabi_gpg_run_service.run_abu_dhabi_gpg_detail_crawl',
		fake_run_abu_dhabi_gpg_detail_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.abu_dhabi_gpg_run_service.ingest_tender',
		fake_ingest_tender,
	)

	result = run_abu_dhabi_gpg_source(session=cast(Session, session))

	assert result.status == 'success'
	assert result.widget_crawled_row_count == 1
	assert result.detail_sampled_row_count == 1
	assert result.enriched_normalized_row_count == 1
	assert result.accepted_row_count == 1
	assert result.review_required_row_count == 0
	assert result.created_tender_count == 1
	assert result.updated_tender_count == 0
	assert source.status == 'healthy'
	assert source.failure_count == 0
	assert source.last_successful_run_at is not None
	assert any(getattr(item, 'status', None) == 'success' for item in session.added)


def test_abu_dhabi_gpg_run_service_failure_marks_source_degraded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])

	async def fake_run_abu_dhabi_gpg_crawl() -> AbuDhabiGPGCrawlResult:
		raise AbuDhabiGPGCrawlerError('blocked by source')

	monkeypatch.setattr(
		'src.crawler.sources.abu_dhabi_gpg_run_service.run_abu_dhabi_gpg_crawl',
		fake_run_abu_dhabi_gpg_crawl,
	)

	result = run_abu_dhabi_gpg_source(session=cast(Session, session))

	assert result.status == 'failed'
	assert result.failure_step == 'widget_crawl'
	assert result.failure_reason == 'blocked by source'
	assert source.status == 'degraded'
	assert source.failure_count == 1
	assert source.last_failed_run_at is not None
	assert any(getattr(item, 'status', None) == 'failed' for item in session.added)
