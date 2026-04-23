from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from src.ai.usage_budget_service import build_ai_daily_budget_snapshot
from src.db.models.ai_control_state import AIControlState
from src.shared.config.settings import Settings, get_settings
from src.shared.schemas.ai_control import (
	AIControlStateResponse,
	AIControlStateUpdateRequest,
)

AI_CONTROL_SINGLETON_ID = 1


@dataclass(frozen=True)
class AIEnrichmentPolicy:
	"""Resolved effective AI enrichment policy used by runtime services."""

	enabled: bool
	reason: str | None
	effective_batch_size: int
	ai_provider: str
	ai_enrichment_enabled: bool
	emergency_stop_enabled: bool
	effective_daily_request_budget: int | None
	effective_daily_reserved_token_budget: int | None
	budget_exhausted: bool
	budget_exhausted_reason: str | None


def get_or_create_ai_control_state(session: Session) -> AIControlState:
	"""Return the singleton AI control state, creating a default row if needed."""
	state = session.get(AIControlState, AI_CONTROL_SINGLETON_ID)
	if state is not None:
		return state

	state = AIControlState(
		id=AI_CONTROL_SINGLETON_ID,
		ai_enrichment_enabled=True,
		emergency_stop_enabled=False,
		emergency_stop_reason=None,
		max_enrichment_batch_size_override=None,
		max_daily_requests_override=None,
		max_daily_reserved_tokens_override=None,
	)
	session.add(state)
	session.flush()
	return state


def update_ai_control_state(
	session: Session,
	*,
	payload: AIControlStateUpdateRequest,
	settings: Settings | None = None,
) -> AIControlStateResponse:
	"""Persist an operator-requested AI control change and return effective state."""
	state = get_or_create_ai_control_state(session)
	state.ai_enrichment_enabled = payload.ai_enrichment_enabled
	state.emergency_stop_enabled = payload.emergency_stop_enabled
	state.emergency_stop_reason = payload.emergency_stop_reason if payload.emergency_stop_enabled else None
	state.max_enrichment_batch_size_override = payload.max_enrichment_batch_size_override
	state.max_daily_requests_override = payload.max_daily_requests_override
	state.max_daily_reserved_tokens_override = payload.max_daily_reserved_tokens_override
	session.flush()
	return build_ai_control_response(session, settings=settings)


def build_ai_control_response(
	session: Session,
	*,
	settings: Settings | None = None,
) -> AIControlStateResponse:
	"""Build the operator-facing AI control response from persisted state."""
	cfg = settings or get_settings()
	state = get_or_create_ai_control_state(session)
	policy = resolve_ai_enrichment_policy(session, settings=cfg)
	today_budget = build_ai_daily_budget_snapshot(
		session,
		settings=cfg,
		request_budget_override=state.max_daily_requests_override,
		reserved_token_budget_override=state.max_daily_reserved_tokens_override,
	)
	return AIControlStateResponse(
		ai_enrichment_enabled=state.ai_enrichment_enabled,
		emergency_stop_enabled=state.emergency_stop_enabled,
		emergency_stop_reason=state.emergency_stop_reason,
		max_enrichment_batch_size_override=state.max_enrichment_batch_size_override,
		max_daily_requests_override=state.max_daily_requests_override,
		max_daily_reserved_tokens_override=state.max_daily_reserved_tokens_override,
		effective_ai_provider=policy.ai_provider,
		effective_ai_enrichment_enabled=policy.enabled,
		effective_enrichment_batch_size=policy.effective_batch_size,
		effective_daily_request_budget=policy.effective_daily_request_budget,
		effective_daily_reserved_token_budget=policy.effective_daily_reserved_token_budget,
		today_usage_date=today_budget.usage_date,
		today_request_count=today_budget.request_count,
		today_blocked_request_count=today_budget.blocked_request_count,
		today_throttled_request_count=today_budget.throttled_request_count,
		today_provider_error_count=today_budget.provider_error_count,
		today_estimated_input_tokens=today_budget.estimated_input_tokens,
		today_reserved_total_tokens=today_budget.reserved_total_tokens,
		today_actual_prompt_tokens=today_budget.actual_prompt_tokens,
		today_actual_completion_tokens=today_budget.actual_completion_tokens,
		today_actual_total_tokens=today_budget.actual_total_tokens,
		budget_exhausted=today_budget.budget_exhausted,
		budget_exhausted_reason=today_budget.budget_exhausted_reason,
		created_at=state.created_at,
		updated_at=state.updated_at,
	)


def resolve_ai_enrichment_policy(
	session: Session,
	*,
	settings: Settings | None = None,
) -> AIEnrichmentPolicy:
	"""Resolve the effective AI enrichment policy from settings plus control state."""
	cfg = settings or get_settings()
	state = get_or_create_ai_control_state(session)
	effective_daily_request_budget = state.max_daily_requests_override
	if effective_daily_request_budget is None:
		effective_daily_request_budget = cfg.ai_daily_request_budget
	effective_daily_reserved_token_budget = state.max_daily_reserved_tokens_override
	if effective_daily_reserved_token_budget is None:
		effective_daily_reserved_token_budget = cfg.ai_daily_reserved_token_budget
	today_budget = build_ai_daily_budget_snapshot(
		session,
		settings=cfg,
		request_budget_override=state.max_daily_requests_override,
		reserved_token_budget_override=state.max_daily_reserved_tokens_override,
	)
	effective_batch_size = cfg.ai_summary_batch_size
	if state.max_enrichment_batch_size_override is not None:
		effective_batch_size = min(
			cfg.ai_summary_batch_size,
			state.max_enrichment_batch_size_override,
		)

	if cfg.ai_provider == 'disabled':
		return AIEnrichmentPolicy(
			enabled=False,
			reason='ai_provider_disabled',
			effective_batch_size=0,
			ai_provider=cfg.ai_provider,
			ai_enrichment_enabled=state.ai_enrichment_enabled,
			emergency_stop_enabled=state.emergency_stop_enabled,
			effective_daily_request_budget=effective_daily_request_budget,
			effective_daily_reserved_token_budget=effective_daily_reserved_token_budget,
			budget_exhausted=today_budget.budget_exhausted,
			budget_exhausted_reason=today_budget.budget_exhausted_reason,
		)

	if not state.ai_enrichment_enabled:
		return AIEnrichmentPolicy(
			enabled=False,
			reason='ai_enrichment_disabled',
			effective_batch_size=0,
			ai_provider=cfg.ai_provider,
			ai_enrichment_enabled=state.ai_enrichment_enabled,
			emergency_stop_enabled=state.emergency_stop_enabled,
			effective_daily_request_budget=effective_daily_request_budget,
			effective_daily_reserved_token_budget=effective_daily_reserved_token_budget,
			budget_exhausted=today_budget.budget_exhausted,
			budget_exhausted_reason=today_budget.budget_exhausted_reason,
		)

	if state.emergency_stop_enabled:
		return AIEnrichmentPolicy(
			enabled=False,
			reason='emergency_stop_enabled',
			effective_batch_size=0,
			ai_provider=cfg.ai_provider,
			ai_enrichment_enabled=state.ai_enrichment_enabled,
			emergency_stop_enabled=state.emergency_stop_enabled,
			effective_daily_request_budget=effective_daily_request_budget,
			effective_daily_reserved_token_budget=effective_daily_reserved_token_budget,
			budget_exhausted=today_budget.budget_exhausted,
			budget_exhausted_reason=today_budget.budget_exhausted_reason,
		)

	if today_budget.budget_exhausted:
		return AIEnrichmentPolicy(
			enabled=False,
			reason=today_budget.budget_exhausted_reason,
			effective_batch_size=0,
			ai_provider=cfg.ai_provider,
			ai_enrichment_enabled=state.ai_enrichment_enabled,
			emergency_stop_enabled=state.emergency_stop_enabled,
			effective_daily_request_budget=effective_daily_request_budget,
			effective_daily_reserved_token_budget=effective_daily_reserved_token_budget,
			budget_exhausted=today_budget.budget_exhausted,
			budget_exhausted_reason=today_budget.budget_exhausted_reason,
		)

	return AIEnrichmentPolicy(
		enabled=True,
		reason=None,
		effective_batch_size=effective_batch_size,
		ai_provider=cfg.ai_provider,
		ai_enrichment_enabled=state.ai_enrichment_enabled,
		emergency_stop_enabled=state.emergency_stop_enabled,
		effective_daily_request_budget=effective_daily_request_budget,
		effective_daily_reserved_token_budget=effective_daily_reserved_token_budget,
		budget_exhausted=today_budget.budget_exhausted,
		budget_exhausted_reason=today_budget.budget_exhausted_reason,
	)
