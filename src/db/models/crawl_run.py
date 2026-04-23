from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class CrawlRun(TimestampMixin, Base):
    """Operational record of a crawl attempt for a monitored source."""

    __tablename__ = "crawl_runs"
    __table_args__ = (
        Index("ix_crawl_runs_source_id", "source_id"),
        Index("ix_crawl_runs_started_at", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    new_tenders_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    crawled_row_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    normalized_row_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    accepted_row_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    review_required_row_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    updated_tender_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    failure_step: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    run_identifier: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
