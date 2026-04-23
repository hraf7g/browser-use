from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
	ARRAY,
	DateTime,
	ForeignKey,
	Index,
	Integer,
	String,
	Text,
	UniqueConstraint,
	text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class Tender(TimestampMixin, Base):
	"""Monitored tender record extracted from sources."""

	__tablename__ = 'tenders'

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		primary_key=True,
		default=uuid.uuid4,
	)
	source_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey('sources.id', ondelete='CASCADE'),
		nullable=False,
		index=True,
	)
	tender_ref: Mapped[str | None] = mapped_column(
		String(100),
		nullable=True,
	)
	source_url: Mapped[str] = mapped_column(
		Text,
		nullable=False,
	)
	title: Mapped[str] = mapped_column(
		String(500),
		nullable=False,
	)
	issuing_entity: Mapped[str] = mapped_column(
		String(255),
		nullable=False,
	)
	closing_date: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True),
		nullable=True,
		index=True,
	)
	opening_date: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True),
		nullable=True,
	)
	published_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True),
		nullable=True,
	)
	category: Mapped[str | None] = mapped_column(
		String(500),
		nullable=True,
	)
	industry_codes: Mapped[list[str]] = mapped_column(
		ARRAY(String(64)),
		nullable=False,
		default=list,
		server_default='{}',
	)
	primary_industry_code: Mapped[str | None] = mapped_column(
		String(64),
		nullable=True,
	)
	ai_summary: Mapped[str | None] = mapped_column(
		Text,
		nullable=True,
	)
	ai_summary_attempt_count: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	ai_summary_generated_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True),
		nullable=True,
	)
	ai_summary_last_attempted_at: Mapped[datetime | None] = mapped_column(
		DateTime(timezone=True),
		nullable=True,
	)
	ai_summary_last_error: Mapped[str | None] = mapped_column(
		Text,
		nullable=True,
	)
	ai_summary_model: Mapped[str | None] = mapped_column(
		String(255),
		nullable=True,
	)
	dedupe_key: Mapped[str] = mapped_column(
		String(255),
		nullable=False,
	)

	# Persisted multilingual-normalized search text for deterministic backend search.
	search_text: Mapped[str] = mapped_column(
		Text,
		nullable=False,
		server_default='',
	)

	__table_args__ = (
		UniqueConstraint(
			'source_id',
			'dedupe_key',
			name='uq_tenders_source_dedupe',
		),
		Index(
			'uq_tenders_source_ref',
			'source_id',
			'tender_ref',
			unique=True,
			postgresql_where=text('tender_ref IS NOT NULL'),
		),
		Index(
			'ix_tenders_created_at',
			'created_at',
		),
		Index(
			'ix_tenders_search_text_trgm',
			'search_text',
			postgresql_using='gin',
			postgresql_ops={'search_text': 'gin_trgm_ops'},
		),
	)
