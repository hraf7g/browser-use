from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
	"""Application user account."""

	__tablename__ = 'users'

	id: Mapped[uuid.UUID] = mapped_column(
		UUID(as_uuid=True),
		primary_key=True,
		default=uuid.uuid4,
	)
	email: Mapped[str] = mapped_column(
		String(320),
		nullable=False,
		unique=True,
		index=True,
	)
	password_hash: Mapped[str] = mapped_column(
		String(255),
		nullable=False,
	)
	is_active: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=True,
		server_default='true',
	)
	is_operator: Mapped[bool] = mapped_column(
		Boolean,
		nullable=False,
		default=False,
		server_default='false',
	)
	last_login_at: Mapped[datetime | None] = mapped_column(
		nullable=True,
	)
