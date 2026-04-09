from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class Source(TimestampMixin, Base):
    """Monitored tender source configuration and health state."""

    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        unique=True,
    )
    base_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="healthy",
        server_default="healthy",
    )
    last_successful_run_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    last_failed_run_at: Mapped[datetime | None] = mapped_column(
        nullable=True,
    )
    failure_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
