from __future__ import annotations

import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

PreferredLanguage = Literal["auto", "ar", "en"]
E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class NotificationPreferenceUpdateRequest(BaseModel):
    """Validated request body for updating a user's notification preferences."""

    model_config = ConfigDict(str_strip_whitespace=True)

    email_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    whatsapp_phone_e164: str | None = Field(default=None, max_length=20)
    daily_brief_enabled: bool | None = None
    instant_alert_enabled: bool | None = None
    preferred_language: PreferredLanguage | None = None

    @field_validator(
        "email_enabled",
        "whatsapp_enabled",
        "daily_brief_enabled",
        "instant_alert_enabled",
        mode="before",
    )
    @classmethod
    def validate_optional_boolean(cls, value: object) -> bool | None:
        if value is None:
            return None

        if not isinstance(value, bool):
            raise ValueError("notification preference boolean fields must be true or false")

        return value

    @field_validator("whatsapp_phone_e164", mode="before")
    @classmethod
    def validate_whatsapp_phone_e164(cls, value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            return None

        if not E164_PATTERN.fullmatch(cleaned):
            raise ValueError("whatsapp_phone_e164 must be a valid E.164 phone number")

        return cleaned


class NotificationPreferenceResponse(BaseModel):
    """Safe notification-preference payload returned by backend services."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: UUID
    email_enabled: bool
    whatsapp_enabled: bool
    whatsapp_phone_e164: str | None = None
    daily_brief_enabled: bool
    instant_alert_enabled: bool
    preferred_language: PreferredLanguage
