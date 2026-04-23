from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.db.models.base import Base, TimestampMixin


class BrowserAgentRun(TimestampMixin, Base):
	"""Persisted browser-agent run requested by an authenticated user."""

	__tablename__ = 'browser_agent_runs'
	__table_args__ = (
		CheckConstraint(
			"status IN ('queued','running','cancelling','cancelled','completed','failed')",
			name='ck_browser_agent_runs_status_valid',
		),
		CheckConstraint('max_steps >= 1', name='ck_browser_agent_runs_max_steps_positive'),
		CheckConstraint('step_timeout_seconds >= 30', name='ck_browser_agent_runs_step_timeout_minimum'),
		CheckConstraint('llm_timeout_seconds >= 15', name='ck_browser_agent_runs_llm_timeout_minimum'),
		Index('ix_browser_agent_runs_user_status', 'user_id', 'status'),
		Index('ix_browser_agent_runs_status_created_at', 'status', 'created_at'),
	)

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		primary_key=True,
		default=uuid.uuid4,
	)
	user_id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		ForeignKey('users.id', ondelete='CASCADE'),
		nullable=False,
		index=True,
	)
	status: Mapped[str] = mapped_column(
		String(32),
		nullable=False,
		default='queued',
		server_default='queued',
		index=True,
	)
	task_prompt: Mapped[str] = mapped_column(
		Text,
		nullable=False,
	)
	start_url: Mapped[str | None] = mapped_column(
		String(2048),
		nullable=True,
	)
	allowed_domains: Mapped[list[str] | None] = mapped_column(
		JSON,
		nullable=True,
	)
	max_steps: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
	)
	step_timeout_seconds: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
	)
	llm_timeout_seconds: Mapped[int] = mapped_column(
		Integer,
		nullable=False,
	)
	queued_at: Mapped[datetime] = mapped_column(
		nullable=False,
	)
	started_at: Mapped[datetime | None] = mapped_column(
		nullable=True,
	)
	finished_at: Mapped[datetime | None] = mapped_column(
		nullable=True,
	)
	cancel_requested_at: Mapped[datetime | None] = mapped_column(
		nullable=True,
	)
	last_heartbeat_at: Mapped[datetime | None] = mapped_column(
		nullable=True,
	)
	error_message: Mapped[str | None] = mapped_column(
		Text,
		nullable=True,
	)
	final_result_text: Mapped[str | None] = mapped_column(
		Text,
		nullable=True,
	)
	llm_provider: Mapped[str] = mapped_column(
		String(64),
		nullable=False,
		default='bedrock_anthropic',
		server_default='bedrock_anthropic',
	)
	llm_model: Mapped[str] = mapped_column(
		String(255),
		nullable=False,
	)
