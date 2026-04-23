from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class AIControlStateUpdateRequest(BaseModel):
	"""Operator-managed update payload for persistent AI control settings."""

	ai_enrichment_enabled: bool
	emergency_stop_enabled: bool
	emergency_stop_reason: str | None = Field(default=None, max_length=2000)
	max_enrichment_batch_size_override: int | None = Field(default=None, ge=1, le=200)
	max_daily_requests_override: int | None = Field(default=None, ge=1, le=1_000_000)
	max_daily_reserved_tokens_override: int | None = Field(default=None, ge=1, le=100_000_000)

	@field_validator('emergency_stop_reason')
	@classmethod
	def normalize_emergency_stop_reason(cls, value: str | None) -> str | None:
		if value is None:
			return None
		cleaned = value.strip()
		return cleaned or None


class AIControlStateResponse(BaseModel):
	"""Operator-facing persisted AI control state with effective runtime policy."""

	ai_enrichment_enabled: bool
	emergency_stop_enabled: bool
	emergency_stop_reason: str | None = None
	max_enrichment_batch_size_override: int | None = Field(default=None, ge=1)
	max_daily_requests_override: int | None = Field(default=None, ge=1)
	max_daily_reserved_tokens_override: int | None = Field(default=None, ge=1)
	effective_ai_provider: str
	effective_ai_enrichment_enabled: bool
	effective_enrichment_batch_size: int = Field(ge=0)
	effective_daily_request_budget: int | None = Field(default=None, ge=1)
	effective_daily_reserved_token_budget: int | None = Field(default=None, ge=1)
	today_usage_date: date
	today_request_count: int = Field(ge=0)
	today_blocked_request_count: int = Field(ge=0)
	today_throttled_request_count: int = Field(ge=0)
	today_provider_error_count: int = Field(ge=0)
	today_estimated_input_tokens: int = Field(ge=0)
	today_reserved_total_tokens: int = Field(ge=0)
	today_actual_prompt_tokens: int = Field(ge=0)
	today_actual_completion_tokens: int = Field(ge=0)
	today_actual_total_tokens: int = Field(ge=0)
	budget_exhausted: bool
	budget_exhausted_reason: str | None = None
	created_at: datetime
	updated_at: datetime
