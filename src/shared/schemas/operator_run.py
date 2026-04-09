from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

SupportedOperatorSourceName = Literal["Dubai eSupply", "Federal MOF"]


class OperatorRunSourceRequest(BaseModel):
    """Validated operator request payload for one manual source run."""

    source_name: SupportedOperatorSourceName


class OperatorRunSourceResponse(BaseModel):
    """Normalized operator response for one manual source run."""

    source_name: SupportedOperatorSourceName
    source_id: UUID
    crawl_run_id: UUID
    run_identifier: str = Field(min_length=1, max_length=100)
    status: str = Field(min_length=1, max_length=32)
    started_at: datetime
    finished_at: datetime
    crawled_row_count: int = Field(ge=0)
    normalized_row_count: int = Field(ge=0)
    accepted_row_count: int = Field(ge=0)
    review_required_row_count: int = Field(ge=0)
    created_tender_count: int = Field(ge=0)
    updated_tender_count: int = Field(ge=0)
    failure_step: str | None = Field(default=None, max_length=100)
    failure_reason: str | None = Field(default=None, max_length=2000)
