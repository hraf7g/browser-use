from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from src.api.services.activity_overview_service import _build_source_card, _build_summary
from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source


def _build_source(*, status: str, last_successful_run_at: datetime | None = None) -> Source:
	return Source(
		id=uuid.uuid4(),
		name=f'Source {uuid.uuid4()}',
		base_url=f'https://{uuid.uuid4()}.example.com',
		country_code='SA',
		country_name='Saudi Arabia',
		lifecycle='live',
		status=status,
		failure_count=0,
		last_successful_run_at=last_successful_run_at,
		last_failed_run_at=None,
		notes=None,
	)


def test_build_summary_counts_degraded_sources_using_canonical_health_vocabulary() -> None:
	now = datetime.now(timezone.utc)
	summary = _build_summary(
		sources=[
			_build_source(status='healthy', last_successful_run_at=now - timedelta(hours=2)),
			_build_source(status='degraded', last_successful_run_at=now - timedelta(hours=1)),
			_build_source(status='failed'),
		]
	)

	assert summary.total_sources == 3
	assert summary.healthy_sources == 1
	assert summary.degraded_sources == 2
	assert summary.latest_successful_check_at == now - timedelta(hours=1)


def test_build_source_card_preserves_failed_run_status_but_normalizes_source_health() -> None:
	source = _build_source(status='failed')
	started_at = datetime.now(timezone.utc)
	latest_run = CrawlRun(
		id=uuid.uuid4(),
		source_id=source.id,
		status='failed',
		started_at=started_at,
		finished_at=started_at + timedelta(minutes=1),
		new_tenders_count=0,
		crawled_row_count=10,
		normalized_row_count=8,
		accepted_row_count=5,
		review_required_row_count=3,
		updated_tender_count=1,
		failure_reason='navigation timeout',
		failure_step='crawl',
		run_identifier='run-1',
	)

	card = _build_source_card(source=source, latest_run=latest_run)

	assert card.source_country_code == 'SA'
	assert card.source_country_name == 'Saudi Arabia'
	assert card.source_lifecycle == 'live'
	assert card.source_status == 'degraded'
	assert card.latest_run_status == 'failed'
	assert card.latest_run_failure_reason == 'navigation timeout'
