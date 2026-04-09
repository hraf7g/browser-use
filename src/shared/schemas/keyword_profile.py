from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

KEYWORD_MAX_ITEMS = 50
KEYWORD_MAX_LENGTH = 100
INDUSTRY_LABEL_MAX_LENGTH = 120


class KeywordProfileUpsertRequest(BaseModel):
    """Validated request body for creating or updating a keyword profile."""

    model_config = ConfigDict(str_strip_whitespace=True)

    keywords: list[str] = Field(default_factory=list)
    alert_enabled: bool = True
    industry_label: str | None = Field(default=None, max_length=INDUSTRY_LABEL_MAX_LENGTH)

    @field_validator("keywords", mode="before")
    @classmethod
    def validate_keywords(cls, value: object) -> list[str]:
        if value is None:
            return []

        if not isinstance(value, list):
            raise ValueError("keywords must be a list of strings")

        normalized: list[str] = []
        seen: set[str] = set()

        for item in value:
            if not isinstance(item, str):
                raise ValueError("each keyword must be a string")

            cleaned = item.strip()
            if not cleaned:
                raise ValueError("keywords must not contain empty values")

            if len(cleaned) > KEYWORD_MAX_LENGTH:
                raise ValueError(
                    f"keyword '{cleaned}' exceeds maximum length of {KEYWORD_MAX_LENGTH}"
                )

            dedupe_key = cleaned.casefold()
            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            normalized.append(cleaned)

        if len(normalized) > KEYWORD_MAX_ITEMS:
            raise ValueError(
                f"keywords must not contain more than {KEYWORD_MAX_ITEMS} items"
            )

        return normalized

    @field_validator("industry_label", mode="before")
    @classmethod
    def normalize_industry_label(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None


class KeywordProfileResponse(BaseModel):
    """Safe keyword profile payload returned by profile endpoints."""

    keywords: list[str]
    alert_enabled: bool
    industry_label: str | None = None
