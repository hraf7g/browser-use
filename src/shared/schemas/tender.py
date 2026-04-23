from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
TenderListSort = Literal['relevance', 'newest', 'closingSoon']


class TenderListQueryParams(BaseModel):
	"""Validated query parameters for listing tenders."""

	model_config = ConfigDict(str_strip_whitespace=True)

	page: int = Field(default=DEFAULT_PAGE, ge=1)
	limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
	source_id: UUID | None = None
	source_ids: list[UUID] = Field(default_factory=list)
	search: str | None = Field(default=None, max_length=255)
	match_only: bool = False
	new_only: bool = False
	closing_soon: bool = False
	sort: TenderListSort = 'relevance'

	@field_validator('search', mode='before')
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
	source_name: str
	source_url: str
	title: str
	issuing_entity: str
	closing_date: datetime | None = None
	created_at: datetime
	category: str | None = None
	industry_codes: list[str] = Field(default_factory=list)
	primary_industry_code: str | None = None
	ai_summary: str | None = None
	tender_ref: str | None = None
	is_matched: bool = False
	matched_keywords: list[str] = Field(default_factory=list)
	matched_country_codes: list[str] = Field(default_factory=list)
	matched_industry_codes: list[str] = Field(default_factory=list)


class TenderListSourceOption(BaseModel):
	"""Available source option for tender filtering."""

	id: UUID
	name: str


class TenderListResponse(BaseModel):
	"""Paginated tenders list response."""

	items: list[TenderListItem]
	available_sources: list[TenderListSourceOption] = Field(default_factory=list)
	total: int = Field(ge=0)
	page: int = Field(ge=1)
	limit: int = Field(ge=1, le=MAX_PAGE_SIZE)
