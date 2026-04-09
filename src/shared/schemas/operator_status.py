from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OperatorSourceStatusItem(BaseModel):
    """Operator-facing health snapshot for one monitored source."""

    source_id: UUID
    source_name: str
    source_base_url: str
    source_status: str
    failure_count: int = Field(ge=0)
    last_successful_run_at: datetime | None = None
    last_failed_run_at: datetime | None = None
    latest_run_id: UUID | None = None
    latest_run_status: str | None = None
    latest_run_started_at: datetime | None = None
    latest_run_finished_at: datetime | None = None
    latest_run_new_tenders_count: int | None = None
    latest_run_failure_reason: str | None = None
    latest_run_failure_step: str | None = None
    latest_run_identifier: str | None = None


class OperatorStatusResponse(BaseModel):
    """Operator-facing aggregated status response."""

    generated_at: datetime
    sources: list[OperatorSourceStatusItem]
