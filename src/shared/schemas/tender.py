from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class TenderListQueryParams(BaseModel):
    """Validated query parameters for listing tenders."""

    model_config = ConfigDict(str_strip_whitespace=True)

    page: int = Field(default=DEFAULT_PAGE, ge=1)
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    source_id: UUID | None = None
    search: str | None = Field(default=None, max_length=255)

    @field_validator("search", mode="before")
    @classmethod
    def normalize_search(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class TenderListItem(BaseModel):
    """Safe tender payload returned in tenders list responses."""

    id: UUID
    source_id: UUID
    source_url: str
    title: str
    issuing_entity: str
    closing_date: datetime
    category: str | None = None
    ai_summary: str | None = None
    tender_ref: str | None = None


class TenderListResponse(BaseModel):
    """Paginated tenders list response."""

    items: list[TenderListItem]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=MAX_PAGE_SIZE)
