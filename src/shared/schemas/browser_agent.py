from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BrowserAgentRunCreateRequest(BaseModel):
	"""Authenticated user request to queue one browser-agent run."""

	model_config = ConfigDict(str_strip_whitespace=True)

	task_prompt: str = Field(min_length=10, max_length=4000)
	start_url: str | None = Field(default=None, max_length=2048)
	allowed_domains: list[str] | None = Field(default=None, max_length=25)
	max_steps: int | None = Field(default=None, ge=1, le=100)

	@field_validator('task_prompt')
	@classmethod
	def validate_task_prompt(cls, value: str) -> str:
		cleaned = value.strip()
		if len(cleaned) < 10:
			raise ValueError('task_prompt must contain at least 10 characters')
		return cleaned

	@field_validator('start_url')
	@classmethod
	def normalize_start_url(cls, value: str | None) -> str | None:
		if value is None:
			return None
		cleaned = value.strip()
		return cleaned or None

	@field_validator('allowed_domains')
	@classmethod
	def normalize_allowed_domains(cls, value: list[str] | None) -> list[str] | None:
		if value is None:
			return None
		normalized = [item.strip() for item in value if item.strip()]
		return normalized or None


class BrowserAgentRunResponse(BaseModel):
	"""API response describing one browser-agent run."""

	id: UUID
	user_id: UUID
	status: str
	task_prompt: str
	start_url: str | None
	allowed_domains: list[str] | None
	max_steps: int
	step_timeout_seconds: int
	llm_timeout_seconds: int
	queued_at: datetime
	started_at: datetime | None
	finished_at: datetime | None
	cancel_requested_at: datetime | None
	last_heartbeat_at: datetime | None
	error_message: str | None
	final_result_text: str | None
	llm_provider: str
	llm_model: str
	created_at: datetime
	updated_at: datetime


class BrowserAgentRunListResponse(BaseModel):
	"""Current-user browser-agent run list plus effective limits."""

	items: list[BrowserAgentRunResponse]
	max_concurrent_runs_per_user: int
	max_queued_runs_per_user: int
	max_global_running_runs: int
	current_user_running_count: int
	current_user_queued_count: int
	global_running_count: int


class BrowserAgentCancelResponse(BaseModel):
	"""Cancellation response for one browser-agent run."""

	run: BrowserAgentRunResponse
	cancelled_immediately: bool
