from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

import pytest

from browser_use.llm.exceptions import ModelRateLimitError
from browser_use.llm.messages import SystemMessage, UserMessage
from browser_use.llm.views import ChatInvokeUsage
from src.ai.usage_budget_service import (
	AIDailyBudgetExceededError,
	build_ai_daily_budget_snapshot,
	get_or_create_ai_daily_usage,
	record_ai_invoke_completion,
	record_ai_invoke_failure,
	reserve_ai_budget_for_messages,
)
from src.db.models.ai_daily_usage import AIDailyUsage
from src.shared.config.settings import Settings

if TYPE_CHECKING:
	from sqlalchemy.orm import Session


class FakeSession:
	def __init__(self):
		self._daily_usage: dict[object, AIDailyUsage] = {}
		self.flush_calls = 0

	def get(self, model: object, identifier: object):
		if model is AIDailyUsage:
			return self._daily_usage.get(identifier)
		return None

	def add(self, instance: object) -> None:
		if isinstance(instance, AIDailyUsage):
			self._daily_usage[instance.usage_date] = instance

	def flush(self) -> None:
		now = datetime.now(UTC)
		self.flush_calls += 1
		for usage in self._daily_usage.values():
			if getattr(usage, 'created_at', None) is None:
				usage.created_at = now
			usage.updated_at = now


def _build_settings() -> Settings:
	return Settings(
		ai_provider='bedrock_anthropic',
		aws_region='us-east-1',
		ai_max_tokens=512,
		ai_daily_request_budget=3,
		ai_daily_reserved_token_budget=2_000,
	)


def _build_messages() -> list[SystemMessage | UserMessage]:
	return [
		SystemMessage(content='Summarize the public tender safely.'),
		UserMessage(content='{"title":"Network monitoring contract"}'),
	]


def test_reserve_ai_budget_for_messages_records_preflight_usage(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	session = FakeSession()
	monkeypatch.setattr(
		'src.ai.usage_budget_service.estimate_bedrock_converse_input_tokens',
		lambda **kwargs: 140,
	)

	reservation = reserve_ai_budget_for_messages(
		cast('Session', session),
		model_id='anthropic.claude-sonnet-4-6',
		messages=_build_messages(),
		settings=_build_settings(),
	)

	assert reservation.estimated_input_tokens == 140
	assert reservation.reserved_total_tokens == 652
	ledger = get_or_create_ai_daily_usage(cast('Session', session))
	assert ledger.request_count == 1
	assert ledger.estimated_input_tokens == 140
	assert ledger.reserved_total_tokens == 652


def test_reserve_ai_budget_for_messages_blocks_when_request_budget_exhausted() -> None:
	session = FakeSession()
	today = datetime.now(UTC).date()
	session.add(
		AIDailyUsage(
			usage_date=today,
			request_count=3,
			blocked_request_count=0,
			throttled_request_count=0,
			provider_error_count=0,
			estimated_input_tokens=0,
			reserved_total_tokens=0,
			actual_prompt_tokens=0,
			actual_completion_tokens=0,
			actual_total_tokens=0,
			last_model=None,
		)
	)

	with pytest.raises(AIDailyBudgetExceededError, match='daily_request_budget_exhausted'):
		reserve_ai_budget_for_messages(
			cast('Session', session),
			model_id='anthropic.claude-sonnet-4-6',
			messages=_build_messages(),
			settings=_build_settings(),
		)

	ledger = get_or_create_ai_daily_usage(cast('Session', session))
	assert ledger.blocked_request_count == 1


def test_reserve_ai_budget_for_messages_blocks_when_reserved_tokens_would_exceed_budget(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	session = FakeSession()
	today = datetime.now(UTC).date()
	session.add(
		AIDailyUsage(
			usage_date=today,
			request_count=1,
			blocked_request_count=0,
			throttled_request_count=0,
			provider_error_count=0,
			estimated_input_tokens=300,
			reserved_total_tokens=1_700,
			actual_prompt_tokens=0,
			actual_completion_tokens=0,
			actual_total_tokens=0,
			last_model=None,
		)
	)
	monkeypatch.setattr(
		'src.ai.usage_budget_service.estimate_bedrock_converse_input_tokens',
		lambda **kwargs: 100,
	)

	with pytest.raises(AIDailyBudgetExceededError, match='daily_reserved_token_budget_exhausted'):
		reserve_ai_budget_for_messages(
			cast('Session', session),
			model_id='anthropic.claude-sonnet-4-6',
			messages=_build_messages(),
			settings=_build_settings(),
		)

	ledger = get_or_create_ai_daily_usage(cast('Session', session))
	assert ledger.blocked_request_count == 1


def test_record_ai_invoke_completion_and_failure_update_daily_usage() -> None:
	session = FakeSession()
	ledger = get_or_create_ai_daily_usage(cast('Session', session))

	record_ai_invoke_completion(
		cast('Session', session),
		model_id='anthropic.claude-sonnet-4-6',
		usage=ChatInvokeUsage(
			prompt_tokens=120,
			prompt_cached_tokens=None,
			prompt_cache_creation_tokens=None,
			prompt_image_tokens=None,
			completion_tokens=80,
			total_tokens=200,
		),
	)
	record_ai_invoke_failure(
		cast('Session', session),
		model_id='anthropic.claude-sonnet-4-6',
		error=ModelRateLimitError('slow down'),
	)

	assert ledger.actual_prompt_tokens == 120
	assert ledger.actual_completion_tokens == 80
	assert ledger.actual_total_tokens == 200
	assert ledger.throttled_request_count == 1


def test_build_ai_daily_budget_snapshot_marks_exhaustion() -> None:
	session = FakeSession()
	today = datetime.now(UTC).date()
	session.add(
		AIDailyUsage(
			usage_date=today,
			request_count=2,
			blocked_request_count=1,
			throttled_request_count=0,
			provider_error_count=0,
			estimated_input_tokens=500,
			reserved_total_tokens=1_500,
			actual_prompt_tokens=300,
			actual_completion_tokens=150,
			actual_total_tokens=450,
			last_model='anthropic.claude-sonnet-4-6',
		)
	)

	snapshot = build_ai_daily_budget_snapshot(
		cast('Session', session),
		settings=_build_settings(),
		request_budget_override=2,
		reserved_token_budget_override=2_000,
	)

	assert snapshot.budget_exhausted is True
	assert snapshot.budget_exhausted_reason == 'daily_request_budget_exhausted'
	assert snapshot.request_count == 2
