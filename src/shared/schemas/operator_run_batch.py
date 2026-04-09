from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.shared.schemas.operator_run import OperatorRunSourceResponse


class OperatorRunAllSourcesResponse(BaseModel):
    """Structured operator response for one sequential manual batch run."""

    started_at: datetime
    finished_at: datetime
    overall_status: Literal["success", "partial_failure", "failed"]
    total_sources: int = Field(ge=0)
    success_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    results: list[OperatorRunSourceResponse]
