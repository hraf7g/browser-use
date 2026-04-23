from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

from sqlalchemy.orm import Session

from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.operator.operator_status_service import list_operator_source_statuses


class _ScalarListResult:
	def __init__(self, values: list[object]):
		self._values = values

	def scalars(self) -> _ScalarListResult:
		return self

	def all(self) -> list[object]:
		return list(self._values)


class _RowListResult:
	def __init__(self, values: list[object]):
		self._values = values

	def all(self) -> list[object]:
		return list(self._values)

	def one(self) -> object:
		if len(self._values) != 1:
			raise AssertionError('expected exactly one row')
		return self._values[0]


class FakeSession:
	def __init__(self, *, execute_results: list[object]):
		self._execute_results = list(execute_results)

	def execute(self, statement: object) -> object:
		if not self._execute_results:
			raise AssertionError('unexpected execute() call')
		return self._execute_results.pop(0)


def _build_source(*, name: str) -> Source:
	return Source(
		id=uuid4(),
		name=name,
		base_url=f'https://{name.lower().replace(" ", "-")}.example.com',
		country_code='AE',
		country_name='United Arab Emirates',
		lifecycle='live',
		status='healthy',
		failure_count=0,
		notes='test source',
	)


def test_list_operator_source_statuses_includes_ai_enrichment_rollups() -> None:
	now = datetime.now(UTC)
	dubai = _build_source(name='Dubai eSupply')
	federal = _build_source(name='Federal MOF')
	latest_run = CrawlRun(
		id=uuid4(),
		source_id=dubai.id,
		status='success',
		started_at=now,
		finished_at=now,
		new_tenders_count=2,
		crawled_row_count=5,
		normalized_row_count=5,
		accepted_row_count=4,
		review_required_row_count=1,
		updated_tender_count=1,
		failure_reason=None,
		failure_step=None,
		run_identifier='dubai-run-1',
	)
	session = FakeSession(
		execute_results=[
			_ScalarListResult([federal, dubai]),
			_RowListResult(
				[
					SimpleNamespace(
						source_id=dubai.id,
						pending_count=1,
						retryable_failed_count=2,
						exhausted_count=3,
						completed_count=4,
						last_attempted_at=now,
						last_generated_at=now,
					)
				]
			),
			_RowListResult(
				[
					SimpleNamespace(
						source_id=dubai.id,
						ai_summary_last_error='bedrock timeout',
						ai_summary_last_attempted_at=now,
					)
				]
			),
			_ScalarListResult([latest_run]),
			_RowListResult(
				[
					SimpleNamespace(
						queued_count=2,
						running_count=1,
						cancelling_count=1,
						completed_last_24h_count=4,
						failed_last_24h_count=1,
						cancelled_last_24h_count=1,
						stale_running_count=1,
						oldest_queued_at=now,
						latest_started_at=now,
						latest_finished_at=now,
					)
				]
			),
		]
	)

	response = list_operator_source_statuses(session=cast(Session, session))

	assert [item.source_name for item in response.sources] == ['Dubai eSupply', 'Federal MOF']

	dubai_item = response.sources[0]
	assert dubai_item.latest_run_identifier == 'dubai-run-1'
	assert dubai_item.ai_enrichment.pending_count == 1
	assert dubai_item.ai_enrichment.retryable_failed_count == 2
	assert dubai_item.ai_enrichment.exhausted_count == 3
	assert dubai_item.ai_enrichment.completed_count == 4
	assert dubai_item.ai_enrichment.last_attempted_at == now
	assert dubai_item.ai_enrichment.last_generated_at == now
	assert dubai_item.ai_enrichment.last_error == 'bedrock timeout'
	assert dubai_item.ai_enrichment.last_error_at == now
	assert response.browser_agent_runtime.queued_count == 2
	assert response.browser_agent_runtime.running_count == 1
	assert response.browser_agent_runtime.cancelling_count == 1
	assert response.browser_agent_runtime.completed_last_24h_count == 4
	assert response.browser_agent_runtime.failed_last_24h_count == 1
	assert response.browser_agent_runtime.cancelled_last_24h_count == 1
	assert response.browser_agent_runtime.stale_running_count == 1
	assert response.browser_agent_runtime.oldest_queued_at == now
	assert response.browser_agent_runtime.latest_started_at == now
	assert response.browser_agent_runtime.latest_finished_at == now

	federal_item = response.sources[1]
	assert federal_item.latest_run_identifier is None
	assert federal_item.ai_enrichment.pending_count == 0
	assert federal_item.ai_enrichment.retryable_failed_count == 0
	assert federal_item.ai_enrichment.exhausted_count == 0
	assert federal_item.ai_enrichment.completed_count == 0
	assert federal_item.ai_enrichment.last_attempted_at is None
	assert federal_item.ai_enrichment.last_generated_at is None
	assert federal_item.ai_enrichment.last_error is None
	assert federal_item.ai_enrichment.last_error_at is None
