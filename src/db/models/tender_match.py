from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class TenderMatch(TimestampMixin, Base):
    """Match between a user keyword profile and a tender."""

    __tablename__ = "tender_matches"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "tender_id",
            name="uq_tender_matches_user_id_tender_id",
        ),
        Index(
            "ix_tender_matches_user_id_sent_at",
            "user_id",
            "sent_at",
        ),
        Index(
            "ix_tender_matches_user_id_alerted_at",
            "user_id",
            "alerted_at",
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
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenders.id", ondelete="CASCADE"),
        nullable=False,
    )
    matched_keywords: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text),
        nullable=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    alerted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
