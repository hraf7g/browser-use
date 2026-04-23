from __future__ import annotations

from datetime import date

from sqlalchemy import CheckConstraint, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class AIDailyUsage(TimestampMixin, Base):
	"""Per-UTC-day AI budget ledger used for hard budget enforcement."""

	__tablename__ = 'ai_daily_usage'

	usage_date: Mapped[date] = mapped_column(
		Date,
		primary_key=True,
	)
	request_count: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	blocked_request_count: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	throttled_request_count: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	provider_error_count: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	estimated_input_tokens: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	reserved_total_tokens: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	actual_prompt_tokens: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	actual_completion_tokens: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	actual_total_tokens: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
		default=0,
		server_default='0',
	)
	last_model: Mapped[str | None] = mapped_column(
		String(255),
		nullable=True,
	)

	__table_args__ = (
		CheckConstraint('request_count >= 0', name='ck_ai_daily_usage_request_count_nonnegative'),
		CheckConstraint('blocked_request_count >= 0', name='ck_ai_daily_usage_blocked_count_nonnegative'),
		CheckConstraint('throttled_request_count >= 0', name='ck_ai_daily_usage_throttled_count_nonnegative'),
		CheckConstraint('provider_error_count >= 0', name='ck_ai_daily_usage_provider_error_count_nonnegative'),
		CheckConstraint('estimated_input_tokens >= 0', name='ck_ai_daily_usage_estimated_input_nonnegative'),
		CheckConstraint('reserved_total_tokens >= 0', name='ck_ai_daily_usage_reserved_total_nonnegative'),
		CheckConstraint('actual_prompt_tokens >= 0', name='ck_ai_daily_usage_actual_prompt_nonnegative'),
		CheckConstraint('actual_completion_tokens >= 0', name='ck_ai_daily_usage_actual_completion_nonnegative'),
		CheckConstraint('actual_total_tokens >= 0', name='ck_ai_daily_usage_actual_total_nonnegative'),
	)
