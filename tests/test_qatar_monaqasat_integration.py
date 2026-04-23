from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.crawler.sources.qatar_monaqasat_crawler import (
	QatarMonaqasatCrawlerError,
	QatarMonaqasatCrawlResult,
	QatarMonaqasatRawItem,
)
from src.crawler.sources.qatar_monaqasat_detail_crawler import (
	QatarMonaqasatDetailCrawlResult,
	QatarMonaqasatDetailItem,
)
from src.crawler.sources.qatar_monaqasat_normalizer import (
	normalize_qatar_monaqasat_item,
)
from src.crawler.sources.qatar_monaqasat_quality import (
	assess_qatar_monaqasat_payload,
)
from src.crawler.sources.qatar_monaqasat_run_service import (
	run_qatar_monaqasat_source,
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


def _build_source(name: str = 'Qatar Monaqasat') -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url='https://monaqasat.mof.gov.qa',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def _build_dashboard_item() -> QatarMonaqasatRawItem:
	return QatarMonaqasatRawItem(
		item_index=0,
		extracted_at=datetime.now(UTC),
		page_url='https://monaqasat.mof.gov.qa/TendersOnlineServices/TechnicallyOpenedTenders/63',
		title_text='Qatar Unmanned Aircraft System Traffic Management (QUTM)',
		detail_url='https://monaqasat.mof.gov.qa/TendersOnlineServices/TenderDetails/656564',
		raw_text='317/2026 Public Tender Qatar Unmanned Aircraft System Traffic Management (QUTM) Civil Aviation Authority Publish date 17/02/2026 Type Public Tender',
		visible_reference='317/2026',
		visible_publish_date='17/02/2026',
		visible_ministry='Civil Aviation Authority',
		visible_tender_type='Public Tender',
	)


def _build_detail_item() -> QatarMonaqasatDetailItem:
	dashboard_item = _build_dashboard_item()
	return QatarMonaqasatDetailItem(
		item_index=dashboard_item.item_index,
		extracted_at=datetime.now(UTC),
		dashboard_title_text=dashboard_item.title_text,
		dashboard_visible_reference=dashboard_item.visible_reference,
		dashboard_visible_publish_date=dashboard_item.visible_publish_date,
		dashboard_visible_ministry=dashboard_item.visible_ministry,
		dashboard_visible_tender_type=dashboard_item.visible_tender_type,
		detail_url=dashboard_item.detail_url,
		final_url=dashboard_item.detail_url,
		detail_page_title='Tender Details - Monaqasat',
		access_status='detail_page',
		detail_title='Qatar Unmanned Aircraft System Traffic Management (QUTM)',
		detail_ministry='Civil Aviation Authority',
		detail_tender_number='317/2026',
		detail_entity_tender_number='19/2025',
		detail_publish_date_raw='17/02/2026',
		detail_closing_date_raw='01/03/2026',
		detail_opening_date_raw='05/03/2026',
		detail_request_types='Suppliers / Service Providers',
		detail_tender_type='Public Tender',
		stronger_fields=('published_at', 'closing_date', 'opening_date'),
		raw_text='Tender Announcement Tender number 317/2026 Ministry Civil Aviation Authority Publish date 17/02/2026 Closing Date 01/03/2026',
	)


def test_qatar_normalizer_parses_visible_detail_dates() -> None:
	source_id = uuid4()
	payload = normalize_qatar_monaqasat_item(
		source_id=source_id,
		item=_build_detail_item(),
	)

	assert payload.source_id == source_id
	assert payload.tender_ref == '317/2026'
	assert payload.category == 'Public Tender'
	assert payload.closing_date is not None
	assert payload.published_at is not None
	assert payload.opening_date is not None
	assert payload.closing_date.tzinfo == UTC


def test_qatar_quality_accepts_strong_detail_payload() -> None:
	payload = normalize_qatar_monaqasat_item(
		source_id=uuid4(),
		item=_build_detail_item(),
	)

	assessment = assess_qatar_monaqasat_payload(payload)

	assert assessment.quality_score >= 70
	assert assessment.is_review_required is False
	assert 'closing_date_missing' not in assessment.quality_flags
	assert 'tender_ref_missing' not in assessment.quality_flags


def test_qatar_run_service_success_persists_counts_and_source_health(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])
	dashboard_item = _build_dashboard_item()
	detail_item = _build_detail_item()

	async def fake_run_qatar_monaqasat_crawl() -> QatarMonaqasatCrawlResult:
		return QatarMonaqasatCrawlResult(
			source_name='Qatar Monaqasat',
			listing_url='https://monaqasat.mof.gov.qa/TendersOnlineServices/TechnicallyOpenedTenders/63',
			final_url='https://monaqasat.mof.gov.qa/TendersOnlineServices/TechnicallyOpenedTenders/63',
			page_title='Tender Details - Monaqasat',
			extracted_at=datetime.now(UTC),
			total_items=1,
			items=(dashboard_item,),
		)

	async def fake_run_qatar_monaqasat_detail_crawl(
		*,
		sample_size: int | None = 5,
		dashboard_items=None,
	) -> QatarMonaqasatDetailCrawlResult:
		assert sample_size is None
		assert tuple(dashboard_items or ()) == (dashboard_item,)
		return QatarMonaqasatDetailCrawlResult(
			source_name='Qatar Monaqasat',
			listing_url='https://monaqasat.mof.gov.qa/TendersOnlineServices/TechnicallyOpenedTenders/63',
			final_listing_url='https://monaqasat.mof.gov.qa/TendersOnlineServices/TechnicallyOpenedTenders/63',
			sample_count=1,
			successful_detail_pages=1,
			extracted_at=datetime.now(UTC),
			items=(detail_item,),
		)

	def fake_ingest_tender(*, session: object, payload: Any) -> tuple[object, bool]:
		return (
			SimpleNamespace(
				search_text='qatar unmanned aircraft system public tender civil aviation authority',
				source_id=source.id,
				title=payload.title,
			),
			True,
		)

	monkeypatch.setattr(
		'src.crawler.sources.qatar_monaqasat_run_service.run_qatar_monaqasat_crawl',
		fake_run_qatar_monaqasat_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.qatar_monaqasat_run_service.run_qatar_monaqasat_detail_crawl',
		fake_run_qatar_monaqasat_detail_crawl,
	)
	monkeypatch.setattr(
		'src.crawler.sources.qatar_monaqasat_run_service.ingest_tender',
		fake_ingest_tender,
	)

	result = run_qatar_monaqasat_source(session=cast(Session, session))

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


def test_qatar_run_service_failure_marks_source_degraded(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	source = _build_source()
	session = FakeSession(execute_results=[_ScalarOneOrNoneResult(source)])

	async def fake_run_qatar_monaqasat_crawl() -> QatarMonaqasatCrawlResult:
		raise QatarMonaqasatCrawlerError('blocked by source')

	monkeypatch.setattr(
		'src.crawler.sources.qatar_monaqasat_run_service.run_qatar_monaqasat_crawl',
		fake_run_qatar_monaqasat_crawl,
	)

	result = run_qatar_monaqasat_source(session=cast(Session, session))

	assert result.status == 'failed'
	assert result.failure_step == 'crawl'
	assert result.failure_reason == 'blocked by source'
	assert source.status == 'degraded'
	assert source.failure_count == 1
	assert source.last_failed_run_at is not None
	assert any(getattr(item, 'status', None) == 'failed' for item in session.added)
