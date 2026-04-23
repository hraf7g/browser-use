from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import lru_cache
from importlib import import_module
from typing import Any, cast

from sqlalchemy.orm import Session

from browser_use.llm.exceptions import ModelRateLimitError
from browser_use.llm.messages import AssistantMessage, BaseMessage, SystemMessage, UserMessage
from browser_use.llm.views import ChatInvokeUsage
from src.db.models.ai_daily_usage import AIDailyUsage
from src.shared.config.settings import Settings, get_settings


class AIDailyBudgetExceededError(RuntimeError):
	"""Raised when a request would exceed the configured daily AI budget."""


@dataclass(frozen=True)
class AIDailyBudgetSnapshot:
	"""Resolved daily AI usage ledger plus effective configured ceilings."""

	usage_date: date
	request_count: int
	blocked_request_count: int
	throttled_request_count: int
	provider_error_count: int
	estimated_input_tokens: int
	reserved_total_tokens: int
	actual_prompt_tokens: int
	actual_completion_tokens: int
	actual_total_tokens: int
	effective_daily_request_budget: int | None
	effective_daily_reserved_token_budget: int | None
	budget_exhausted: bool
	budget_exhausted_reason: str | None


@dataclass(frozen=True)
class AIBudgetReservation:
	"""Reservation recorded before a Bedrock model invocation starts."""

	usage_date: date
	model_id: str
	estimated_input_tokens: int
	reserved_total_tokens: int


def get_or_create_ai_daily_usage(session: Session, *, usage_date: date | None = None) -> AIDailyUsage:
	"""Return the UTC-day AI usage ledger row, creating a zeroed row if missing."""
	day = usage_date or datetime.now(UTC).date()
	usage = session.get(AIDailyUsage, day)
	if usage is not None:
		return usage

	usage = AIDailyUsage(
		usage_date=day,
		request_count=0,
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
	session.add(usage)
	session.flush()
	return usage


def build_ai_daily_budget_snapshot(
	session: Session,
	*,
	settings: Settings | None = None,
	usage_date: date | None = None,
	request_budget_override: int | None = None,
	reserved_token_budget_override: int | None = None,
) -> AIDailyBudgetSnapshot:
	"""Build the current UTC-day AI budget snapshot used by operator surfaces."""
	cfg = settings or get_settings()
	usage = get_or_create_ai_daily_usage(session, usage_date=usage_date)
	effective_daily_request_budget = request_budget_override
	if effective_daily_request_budget is None:
		effective_daily_request_budget = cfg.ai_daily_request_budget
	effective_daily_reserved_token_budget = reserved_token_budget_override
	if effective_daily_reserved_token_budget is None:
		effective_daily_reserved_token_budget = cfg.ai_daily_reserved_token_budget

	budget_exhausted = False
	budget_exhausted_reason = None
	if effective_daily_request_budget is not None and usage.request_count >= effective_daily_request_budget:
		budget_exhausted = True
		budget_exhausted_reason = 'daily_request_budget_exhausted'
	elif (
		effective_daily_reserved_token_budget is not None and usage.reserved_total_tokens >= effective_daily_reserved_token_budget
	):
		budget_exhausted = True
		budget_exhausted_reason = 'daily_reserved_token_budget_exhausted'

	return AIDailyBudgetSnapshot(
		usage_date=usage.usage_date,
		request_count=usage.request_count,
		blocked_request_count=usage.blocked_request_count,
		throttled_request_count=usage.throttled_request_count,
		provider_error_count=usage.provider_error_count,
		estimated_input_tokens=usage.estimated_input_tokens,
		reserved_total_tokens=usage.reserved_total_tokens,
		actual_prompt_tokens=usage.actual_prompt_tokens,
		actual_completion_tokens=usage.actual_completion_tokens,
		actual_total_tokens=usage.actual_total_tokens,
		effective_daily_request_budget=effective_daily_request_budget,
		effective_daily_reserved_token_budget=effective_daily_reserved_token_budget,
		budget_exhausted=budget_exhausted,
		budget_exhausted_reason=budget_exhausted_reason,
	)


def reserve_ai_budget_for_messages(
	session: Session,
	*,
	model_id: str,
	messages: Sequence[BaseMessage],
	settings: Settings | None = None,
	request_budget_override: int | None = None,
	reserved_token_budget_override: int | None = None,
) -> AIBudgetReservation:
	"""
	Reserve daily AI budget before a Bedrock invocation starts.

	This uses Bedrock `CountTokens` plus `ai_max_tokens` to match Bedrock's own
	initial quota deduction model more closely than post-hoc accounting alone.
	"""
	cfg = settings or get_settings()
	usage = get_or_create_ai_daily_usage(session)
	effective_daily_request_budget = request_budget_override
	if effective_daily_request_budget is None:
		effective_daily_request_budget = cfg.ai_daily_request_budget
	effective_daily_reserved_token_budget = reserved_token_budget_override
	if effective_daily_reserved_token_budget is None:
		effective_daily_reserved_token_budget = cfg.ai_daily_reserved_token_budget

	if effective_daily_request_budget is not None and usage.request_count >= effective_daily_request_budget:
		usage.blocked_request_count += 1
		session.flush()
		raise AIDailyBudgetExceededError('daily_request_budget_exhausted')

	estimated_input_tokens = estimate_bedrock_converse_input_tokens(
		model_id=model_id,
		messages=messages,
		settings=cfg,
	)
	reserved_total_tokens = estimated_input_tokens + cfg.ai_max_tokens
	if (
		effective_daily_reserved_token_budget is not None
		and usage.reserved_total_tokens + reserved_total_tokens > effective_daily_reserved_token_budget
	):
		usage.blocked_request_count += 1
		session.flush()
		raise AIDailyBudgetExceededError('daily_reserved_token_budget_exhausted')

	usage.request_count += 1
	usage.estimated_input_tokens += estimated_input_tokens
	usage.reserved_total_tokens += reserved_total_tokens
	usage.last_model = model_id
	session.flush()
	return AIBudgetReservation(
		usage_date=usage.usage_date,
		model_id=model_id,
		estimated_input_tokens=estimated_input_tokens,
		reserved_total_tokens=reserved_total_tokens,
	)


def record_ai_invoke_completion(
	session: Session,
	*,
	usage: ChatInvokeUsage,
	model_id: str,
	usage_date: date | None = None,
) -> None:
	"""Persist actual model token usage after a successful invocation."""
	ledger = get_or_create_ai_daily_usage(session, usage_date=usage_date)
	ledger.actual_prompt_tokens += usage.prompt_tokens
	ledger.actual_completion_tokens += usage.completion_tokens
	ledger.actual_total_tokens += usage.total_tokens
	ledger.last_model = model_id
	session.flush()


def record_ai_invoke_failure(
	session: Session,
	*,
	error: Exception,
	model_id: str,
	usage_date: date | None = None,
) -> None:
	"""Persist model failure counters after a reserved invocation fails."""
	ledger = get_or_create_ai_daily_usage(session, usage_date=usage_date)
	if isinstance(error, ModelRateLimitError):
		ledger.throttled_request_count += 1
	else:
		ledger.provider_error_count += 1
	ledger.last_model = model_id
	session.flush()


def estimate_bedrock_converse_input_tokens(
	*,
	model_id: str,
	messages: Sequence[BaseMessage],
	settings: Settings | None = None,
) -> int:
	"""Estimate Bedrock input tokens for a message list using the official CountTokens API."""
	cfg = settings or get_settings()
	client = _get_bedrock_runtime_client(cfg.aws_region)
	response = client.count_tokens(
		modelId=model_id,
		input={
			'converse': _serialize_converse_count_tokens_input(messages),
		},
	)
	return int(response['inputTokens'])


@lru_cache(maxsize=4)
def _get_bedrock_runtime_client(region_name: str) -> Any:
	try:
		boto3 = import_module('boto3')
	except ImportError as exc:
		raise RuntimeError(
			'Amazon Bedrock budget enforcement requires boto3. Install AWS dependencies with `uv sync --extra aws`.'
		) from exc
	return boto3.client('bedrock-runtime', region_name=region_name)


def _serialize_converse_count_tokens_input(
	messages: Sequence[BaseMessage],
) -> dict[str, object]:
	system_blocks: list[dict[str, str]] = []
	conversation_messages: list[dict[str, object]] = []
	for message in messages:
		if isinstance(message, SystemMessage):
			system_blocks.append({'text': message.text})
			continue

		if isinstance(message, UserMessage):
			conversation_messages.append(
				{
					'role': 'user',
					'content': [{'text': message.text}],
				}
			)
			continue

		if isinstance(message, AssistantMessage):
			assistant_text = message.text or message.refusal or ''
			conversation_messages.append(
				{
					'role': 'assistant',
					'content': [{'text': assistant_text}],
				}
			)
			continue

		raise TypeError(f'unsupported message type for Bedrock CountTokens: {type(message)!r}')

	payload: dict[str, object] = {
		'messages': conversation_messages,
	}
	if system_blocks:
		payload['system'] = cast(object, system_blocks)
	return payload
