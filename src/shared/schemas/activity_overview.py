from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.shared.source_registry import SourceHealthStatus

ActivityEventKind = Literal[
	'source_checked',
	'source_failed',
	'match_created',
	'instant_alert_sent',
	'daily_brief_sent',
]


class ActivityOverviewSummary(BaseModel):
	"""High-level user-facing monitoring summary."""

	total_sources: int = Field(ge=0)
	healthy_sources: int = Field(ge=0)
	degraded_sources: int = Field(ge=0)
	latest_successful_check_at: datetime | None = None


class ActivitySourceCard(BaseModel):
	"""User-facing source monitoring card."""

	source_id: UUID
	source_name: str
	source_country_code: str
	source_country_name: str
	source_lifecycle: str
	source_status: SourceHealthStatus
	failure_count: int = Field(ge=0)
	last_successful_run_at: datetime | None = None
	last_failed_run_at: datetime | None = None
	latest_run_status: str | None = None
	latest_run_started_at: datetime | None = None
	latest_run_finished_at: datetime | None = None
	latest_run_new_tenders_count: int | None = None
	latest_run_updated_tender_count: int | None = None
	latest_run_crawled_row_count: int | None = None
	latest_run_normalized_row_count: int | None = None
	latest_run_accepted_row_count: int | None = None
	latest_run_review_required_row_count: int | None = None
	latest_run_failure_step: str | None = None
	latest_run_failure_reason: str | None = None


class ActivityRecentRunItem(BaseModel):
	"""Deterministic record for a recent source run."""

	id: UUID
	source_id: UUID
	source_name: str
	status: str
	started_at: datetime
	finished_at: datetime | None = None
	new_tenders_count: int | None = None
	failure_reason: str | None = None


class ActivityFeedItem(BaseModel):
	"""User-facing activity feed entry derived from persisted facts."""

	id: str
	kind: ActivityEventKind
	status: str
	timestamp: datetime
	title: str
	summary: str | None = None
	source_id: UUID | None = None
	source_name: str | None = None
	tender_id: UUID | None = None
	tender_title: str | None = None
	matched_keywords: list[str] = Field(default_factory=list)
	matched_country_codes: list[str] = Field(default_factory=list)
	matched_industry_codes: list[str] = Field(default_factory=list)
	metadata: dict[str, Any] = Field(default_factory=dict)


class ActivityOverviewResponse(BaseModel):
	"""Authenticated activity and source-monitoring payload."""

	generated_at: datetime
	summary: ActivityOverviewSummary
	sources: list[ActivitySourceCard]
	recent_runs: list[ActivityRecentRunItem]
	activity_items: list[ActivityFeedItem]
