from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.shared.source_registry import SourceHealthStatus


class OperatorSourceAIEnrichmentStatus(BaseModel):
	"""Operator-facing AI enrichment snapshot for one monitored source."""

	pending_count: int = Field(ge=0)
	retryable_failed_count: int = Field(ge=0)
	exhausted_count: int = Field(ge=0)
	completed_count: int = Field(ge=0)
	last_attempted_at: datetime | None = None
	last_generated_at: datetime | None = None
	last_error: str | None = None
	last_error_at: datetime | None = None


class OperatorSourceStatusItem(BaseModel):
	"""Operator-facing health snapshot for one monitored source."""

	source_id: UUID
	source_name: str
	source_base_url: str
	source_country_code: str
	source_country_name: str
	source_lifecycle: str
	source_status: SourceHealthStatus
	failure_count: int = Field(ge=0)
	last_successful_run_at: datetime | None = None
	last_failed_run_at: datetime | None = None
	latest_run_id: UUID | None = None
	latest_run_status: str | None = None
	latest_run_started_at: datetime | None = None
	latest_run_finished_at: datetime | None = None
	latest_run_new_tenders_count: int | None = None
	latest_run_crawled_row_count: int | None = None
	latest_run_normalized_row_count: int | None = None
	latest_run_accepted_row_count: int | None = None
	latest_run_review_required_row_count: int | None = None
	latest_run_updated_tender_count: int | None = None
	latest_run_failure_reason: str | None = None
	latest_run_failure_step: str | None = None
	latest_run_identifier: str | None = None
	ai_enrichment: OperatorSourceAIEnrichmentStatus


class OperatorBrowserAgentRuntimeStatus(BaseModel):
	"""Operator-facing runtime status for live browser-agent execution."""

	queued_count: int = Field(ge=0)
	running_count: int = Field(ge=0)
	cancelling_count: int = Field(ge=0)
	completed_last_24h_count: int = Field(ge=0)
	failed_last_24h_count: int = Field(ge=0)
	cancelled_last_24h_count: int = Field(ge=0)
	stale_running_count: int = Field(ge=0)
	oldest_queued_at: datetime | None = None
	latest_started_at: datetime | None = None
	latest_finished_at: datetime | None = None
	max_global_running_runs: int = Field(ge=1)
	worker_stale_heartbeat_seconds: int = Field(ge=60)


class OperatorStatusResponse(BaseModel):
	"""Operator-facing aggregated status response."""

	generated_at: datetime
	browser_agent_runtime: OperatorBrowserAgentRuntimeStatus
	sources: list[OperatorSourceStatusItem]
