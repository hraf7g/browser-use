from __future__ import annotations

import uuid
from typing import Literal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin

PreferredLanguage = Literal["auto", "ar", "en"]
PREFERRED_LANGUAGE_VALUES: tuple[PreferredLanguage, ...] = ("auto", "ar", "en")


class NotificationPreference(TimestampMixin, Base):
    """Per-user notification channel and language preferences."""

    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_notification_preferences_user_id"),
        CheckConstraint(
            "preferred_language IN ('auto', 'ar', 'en')",
            name="ck_notification_preferences_preferred_language",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    whatsapp_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    whatsapp_phone_e164: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    daily_brief_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    instant_alert_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    preferred_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="auto",
        server_default="auto",
    )
