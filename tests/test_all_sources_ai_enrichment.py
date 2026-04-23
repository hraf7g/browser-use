from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.ai.tender_enrichment_service import TenderEnrichmentResult
from src.operator.all_sources_run_service import run_all_supported_sources_with_isolated_transactions
from src.shared.schemas.operator_run import OperatorRunSourceResponse


class FakeSession(AbstractContextManager['FakeSession']):
	def commit(self) -> None:
		pass

	def rollback(self) -> None:
		pass

	def __exit__(self, exc_type, exc, tb) -> bool:
		return False


class FakeSessionFactory:
	def __call__(self) -> FakeSession:
		return FakeSession()


def _build_result(source_name: str) -> OperatorRunSourceResponse:
	now = datetime.now(UTC)
	return OperatorRunSourceResponse(
		source_name=source_name,
		source_id=uuid4(),
		crawl_run_id=uuid4(),
		run_identifier=f'{source_name.lower().replace(" ", "-")}-run',
		status='success',
		started_at=now,
		finished_at=now,
		crawled_row_count=1,
		normalized_row_count=1,
		accepted_row_count=1,
		review_required_row_count=0,
		created_tender_count=1,
		updated_tender_count=0,
		failure_step=None,
		failure_reason=None,
	)


def test_run_all_sources_with_isolated_transactions_runs_ai_enrichment_after_batch(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setattr(
		'src.operator.all_sources_run_service.SUPPORTED_SOURCE_RUN_ORDER',
		('Dubai eSupply', 'Federal MOF'),
	)
	monkeypatch.setattr(
		'src.operator.all_sources_run_service.dispatch_source_run',
		lambda *, session, source_name: _build_result(source_name),
	)
	calls: list[datetime] = []
	monkeypatch.setattr(
		'src.operator.all_sources_run_service.run_enrich_recent_tenders_job',
		lambda *, since: calls.append(since) or TenderEnrichmentResult(
			attempted_count=2,
			enriched_count=2,
			failed_count=0,
			skipped_count=0,
		),
	)

	result = run_all_supported_sources_with_isolated_transactions(
		session_factory=FakeSessionFactory(),
	)

	assert result.overall_status == 'success'
	assert result.total_sources == 2
	assert len(calls) == 1
	assert isinstance(calls[0], datetime)


def test_run_all_sources_with_isolated_transactions_does_not_fail_when_ai_enrichment_errors(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setattr(
		'src.operator.all_sources_run_service.SUPPORTED_SOURCE_RUN_ORDER',
		('Dubai eSupply',),
	)
	monkeypatch.setattr(
		'src.operator.all_sources_run_service.dispatch_source_run',
		lambda *, session, source_name: _build_result(source_name),
	)
	monkeypatch.setattr(
		'src.operator.all_sources_run_service.run_enrich_recent_tenders_job',
		lambda *, since: (_ for _ in ()).throw(RuntimeError('bedrock failed')),
	)

	result = run_all_supported_sources_with_isolated_transactions(
		session_factory=FakeSessionFactory(),
	)

	assert result.overall_status == 'success'
	assert result.total_sources == 1
