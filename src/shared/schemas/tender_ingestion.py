from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TenderIngestionInput(BaseModel):
    """Validated payload for ingesting a normalized tender record."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source_id: UUID
    source_url: str = Field(min_length=1, max_length=1000)
    title: str = Field(min_length=1, max_length=1000)
    issuing_entity: str = Field(min_length=1, max_length=500)
    closing_date: datetime
    dedupe_key: str = Field(min_length=1, max_length=255)

    tender_ref: str | None = Field(default=None, max_length=255)
    opening_date: datetime | None = None
    published_at: datetime | None = None
    category: str | None = Field(default=None, max_length=255)
    ai_summary: str | None = None

    @field_validator("source_url", "title", "issuing_entity", "dedupe_key")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be empty")
        return cleaned

    @field_validator("tender_ref", "category", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("ai_summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
