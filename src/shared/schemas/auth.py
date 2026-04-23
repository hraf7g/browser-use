from __future__ import annotations

import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_MAX_LENGTH = 320
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

_EMAIL_REGEX = re.compile(
	r'^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,63}$',
	re.IGNORECASE,
)


class SignupRequest(BaseModel):
	"""Validated request body for user registration."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: str = Field(min_length=3, max_length=EMAIL_MAX_LENGTH)
	password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

	@field_validator('email')
	@classmethod
	def validate_email(cls, value: str) -> str:
		normalized = value.strip().lower()
		if not normalized:
			raise ValueError('email must not be empty')
		if len(normalized) > EMAIL_MAX_LENGTH:
			raise ValueError('email is too long')
		if not _EMAIL_REGEX.fullmatch(normalized):
			raise ValueError('email format is invalid')
		return normalized

	@field_validator('password')
	@classmethod
	def validate_password(cls, value: str) -> str:
		if not value:
			raise ValueError('password must not be empty')
		if value != value.strip():
			raise ValueError('password must not start or end with whitespace')
		return value


class LoginRequest(BaseModel):
	"""Validated request body for user login."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: str = Field(min_length=3, max_length=EMAIL_MAX_LENGTH)
	password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)

	@field_validator('email')
	@classmethod
	def validate_email(cls, value: str) -> str:
		normalized = value.strip().lower()
		if not normalized:
			raise ValueError('email must not be empty')
		if len(normalized) > EMAIL_MAX_LENGTH:
			raise ValueError('email is too long')
		if not _EMAIL_REGEX.fullmatch(normalized):
			raise ValueError('email format is invalid')
		return normalized

	@field_validator('password')
	@classmethod
	def validate_password(cls, value: str) -> str:
		if not value:
			raise ValueError('password must not be empty')
		return value


class UserSummary(BaseModel):
	"""Safe user payload returned by auth endpoints."""

	id: UUID
	email: str
	is_active: bool
	is_operator: bool


class SessionStatusResponse(BaseModel):
	"""Safe auth session probe payload for public clients."""

	authenticated: bool
	user: UserSummary | None = None


class ForgotPasswordRequest(BaseModel):
	"""Validated request body for password reset initiation."""

	model_config = ConfigDict(str_strip_whitespace=True)

	email: str = Field(min_length=3, max_length=EMAIL_MAX_LENGTH)

	@field_validator('email')
	@classmethod
	def validate_email(cls, value: str) -> str:
		normalized = value.strip().lower()
		if not normalized:
			raise ValueError('email must not be empty')
		if len(normalized) > EMAIL_MAX_LENGTH:
			raise ValueError('email is too long')
		if not _EMAIL_REGEX.fullmatch(normalized):
			raise ValueError('email format is invalid')
		return normalized


class ForgotPasswordResponse(BaseModel):
	"""Generic password reset request response."""

	accepted: bool = True
	message: str
	delivery_channel: str


class ResetPasswordRequest(BaseModel):
	"""Validated request body for password reset completion."""

	model_config = ConfigDict(str_strip_whitespace=True)

	token: str = Field(min_length=1, max_length=2048)
	password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

	@field_validator('token')
	@classmethod
	def validate_token(cls, value: str) -> str:
		cleaned = value.strip()
		if not cleaned:
			raise ValueError('token must not be empty')
		return cleaned

	@field_validator('password')
	@classmethod
	def validate_password(cls, value: str) -> str:
		if not value:
			raise ValueError('password must not be empty')
		if value != value.strip():
			raise ValueError('password must not start or end with whitespace')
		return value


class ResetPasswordResponse(BaseModel):
	"""Password reset completion response."""

	message: str
