from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_SUBJECT_MAX_LENGTH = 255
EMAIL_RECIPIENT_MAX_LENGTH = 320


class EmailMessage(BaseModel):
    """Normalized email payload for local/dev and future production backends."""

    model_config = ConfigDict(str_strip_whitespace=True)

    to: str = Field(min_length=3, max_length=EMAIL_RECIPIENT_MAX_LENGTH)
    subject: str = Field(min_length=1, max_length=EMAIL_SUBJECT_MAX_LENGTH)
    body_text: str = Field(min_length=1)

    @field_validator("to")
    @classmethod
    def validate_recipient(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("email recipient must not be empty")
        if "@" not in normalized:
            raise ValueError("email recipient format is invalid")
        return normalized

    @field_validator("subject", "body_text")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value must not be empty")
        return cleaned
