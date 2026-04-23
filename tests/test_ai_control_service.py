from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest

from src.ai.control_service import (
	AI_CONTROL_SINGLETON_ID,
	build_ai_control_response,
	resolve_ai_enrichment_policy,
	update_ai_control_state,
)
from src.ai.tender_enrichment_service import enrich_tenders_updated_since
from src.db.models.ai_control_state import AIControlState
from src.db.models.ai_daily_usage import AIDailyUsage
from src.db.models.tender import Tender
from src.shared.config.settings import Settings
from src.shared.schemas.ai_control import AIControlStateUpdateRequest

if TYPE_CHECKING:
	from sqlalchemy.orm import Session


class FakeSession:
	def __init__(self, *, tenders: list[Tender] | None = None):
		self._state: AIControlState | None = None
		self._daily_usage: dict[object, AIDailyUsage] = {}
		self._tenders = tenders or []
		self.flush_calls = 0

	def get(self, model: object, identifier: object):
		if model is AIControlState and identifier == AI_CONTROL_SINGLETON_ID:
			return self._state
		if model is AIDailyUsage:
			return self._daily_usage.get(identifier)
		return None

	def add(self, instance: object) -> None:
		if isinstance(instance, AIControlState):
			self._state = instance
		if isinstance(instance, AIDailyUsage):
			self._daily_usage[instance.usage_date] = instance

	def flush(self) -> None:
		now = datetime.now(UTC)
		self.flush_calls += 1
		if self._state is not None:
			if getattr(self._state, 'created_at', None) is None:
				self._state.created_at = now
			self._state.updated_at = now
		for usage in self._daily_usage.values():
			if getattr(usage, 'created_at', None) is None:
				usage.created_at = now
			usage.updated_at = now

	def execute(self, statement: object):
		class _ScalarListResult:
			def __init__(self, values: Sequence[object]):
				self._values = values

			def scalars(self):
				return self

			def all(self):
				return list(self._values)

		return _ScalarListResult(self._tenders)


def _build_settings() -> Settings:
	return Settings(
		ai_provider='bedrock_anthropic',
		aws_region='us-east-1',
		ai_summary_batch_size=25,
		ai_summary_max_attempts=3,
		ai_daily_request_budget=100,
		ai_daily_reserved_token_budget=100_000,
	)


def _build_tender() -> Tender:
	now = datetime.now(UTC)
	return Tender(
		id=uuid4(),
		source_id=uuid4(),
		source_url='https://example.gov/tenders/123',
		title='Digital platform modernization',
		issuing_entity='National Digital Authority',
		closing_date=now + timedelta(days=7),
		opening_date=now - timedelta(days=1),
		published_at=now - timedelta(days=2),
		category='Technology',
		industry_codes=[],
		primary_industry_code=None,
		ai_summary=None,
		ai_summary_attempt_count=0,
		ai_summary_generated_at=None,
		ai_summary_last_attempted_at=None,
		ai_summary_last_error=None,
		ai_summary_model=None,
		dedupe_key='dedupe-123',
		search_text='digital platform modernization',
		created_at=now - timedelta(hours=3),
		updated_at=now - timedelta(minutes=10),
	)


def test_build_ai_control_response_creates_default_enabled_state() -> None:
	session = FakeSession()

	response = build_ai_control_response(
		cast('Session', session),
		settings=_build_settings(),
	)

	assert response.ai_enrichment_enabled is True
	assert response.emergency_stop_enabled is False
	assert response.effective_ai_enrichment_enabled is True
	assert response.effective_enrichment_batch_size == 25
	assert response.effective_ai_provider == 'bedrock_anthropic'
	assert response.effective_daily_request_budget == 100
	assert response.effective_daily_reserved_token_budget == 100_000
	assert response.today_request_count == 0
	assert response.budget_exhausted is False


def test_update_ai_control_state_applies_emergency_stop_and_batch_override() -> None:
	session = FakeSession()

	response = update_ai_control_state(
		cast('Session', session),
		payload=AIControlStateUpdateRequest(
			ai_enrichment_enabled=True,
			emergency_stop_enabled=True,
			emergency_stop_reason='Operator emergency stop',
			max_enrichment_batch_size_override=5,
			max_daily_requests_override=9,
			max_daily_reserved_tokens_override=10_000,
		),
		settings=_build_settings(),
	)

	assert response.emergency_stop_enabled is True
	assert response.emergency_stop_reason == 'Operator emergency stop'
	assert response.max_enrichment_batch_size_override == 5
	assert response.max_daily_requests_override == 9
	assert response.max_daily_reserved_tokens_override == 10_000
	assert response.effective_ai_enrichment_enabled is False
	assert response.effective_enrichment_batch_size == 0
	assert response.effective_daily_request_budget == 9
	assert response.effective_daily_reserved_token_budget == 10_000


def test_resolve_ai_enrichment_policy_uses_smaller_override() -> None:
	session = FakeSession()
	update_ai_control_state(
		cast('Session', session),
		payload=AIControlStateUpdateRequest(
			ai_enrichment_enabled=True,
			emergency_stop_enabled=False,
			emergency_stop_reason=None,
			max_enrichment_batch_size_override=7,
		),
		settings=_build_settings(),
	)

	policy = resolve_ai_enrichment_policy(
		cast('Session', session),
		settings=_build_settings(),
	)

	assert policy.enabled is True
	assert policy.effective_batch_size == 7
	assert policy.reason is None


def test_resolve_ai_enrichment_policy_disables_when_daily_budget_exhausted() -> None:
	session = FakeSession()
	today = datetime.now(UTC).date()
	session.add(
		AIDailyUsage(
			usage_date=today,
			request_count=100,
			blocked_request_count=0,
			throttled_request_count=0,
			provider_error_count=0,
			estimated_input_tokens=12_000,
			reserved_total_tokens=20_000,
			actual_prompt_tokens=7_000,
			actual_completion_tokens=1_000,
			actual_total_tokens=8_000,
			last_model='anthropic.claude-sonnet-4-6',
		)
	)

	policy = resolve_ai_enrichment_policy(
		cast('Session', session),
		settings=_build_settings(),
	)

	assert policy.enabled is False
	assert policy.reason == 'daily_request_budget_exhausted'
	assert policy.budget_exhausted is True


def test_enrich_tenders_updated_since_skips_when_emergency_stop_enabled(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	tender = _build_tender()
	session = FakeSession(tenders=[tender])
	update_ai_control_state(
		cast('Session', session),
		payload=AIControlStateUpdateRequest(
			ai_enrichment_enabled=True,
			emergency_stop_enabled=True,
			emergency_stop_reason='stop now',
			max_enrichment_batch_size_override=None,
		),
		settings=_build_settings(),
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.build_ai_runtime',
		lambda settings: (_ for _ in ()).throw(AssertionError('build_ai_runtime must not be called')),
	)

	result = enrich_tenders_updated_since(
		cast('Session', session),
		since=datetime.now(UTC) - timedelta(days=1),
		settings=_build_settings(),
	)

	assert result.attempted_count == 0
	assert result.enriched_count == 0
	assert tender.ai_summary is None
