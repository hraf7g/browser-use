from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class KeywordProfile(TimestampMixin, Base):
    """Keyword profile for matching tenders to a user."""

    __tablename__ = "keyword_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_keyword_profiles_user_id"),
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
    keywords: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
    )
    alert_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    industry_label: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
