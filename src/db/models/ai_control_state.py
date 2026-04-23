from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class AIControlState(TimestampMixin, Base):
	"""Singleton operator-managed control plane for AI execution policy."""

	__tablename__ = 'ai_control_state'

	id: Mapped[int] = mapped_column(
		Integer,
		primary_key=True,
		default=1,
	)
	ai_enrichment_enabled: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=True,
		server_default='true',
	)
	emergency_stop_enabled: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=False,
		server_default='false',
	)
	emergency_stop_reason: Mapped[str | None] = mapped_column(
		Text,
		nullable=True,
	)
	max_enrichment_batch_size_override: Mapped[int | None] = mapped_column(
		Integer,
		nullable=True,
	)
	max_daily_requests_override: Mapped[int | None] = mapped_column(
		Integer,
		nullable=True,
	)
	max_daily_reserved_tokens_override: Mapped[int | None] = mapped_column(
		Integer,
		nullable=True,
	)

	__table_args__ = (
		CheckConstraint('id = 1', name='ck_ai_control_state_singleton'),
		CheckConstraint(
			'max_enrichment_batch_size_override IS NULL OR max_enrichment_batch_size_override >= 1',
			name='ck_ai_control_state_batch_override_positive',
		),
		CheckConstraint(
			'max_daily_requests_override IS NULL OR max_daily_requests_override >= 1',
			name='ck_ai_control_state_daily_requests_override_positive',
		),
		CheckConstraint(
			'max_daily_reserved_tokens_override IS NULL OR max_daily_reserved_tokens_override >= 1',
			name='ck_ai_control_state_daily_reserved_tokens_override_positive',
		),
	)
