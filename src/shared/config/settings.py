from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Application settings loaded from environment variables."""

	model_config = SettingsConfigDict(
		env_prefix='UTW_',
		env_file='.env',
		env_file_encoding='utf-8',
		extra='ignore',
		case_sensitive=False,
	)

	app_name: str = Field(default='UAE Tender Watch')
	environment: Literal['development', 'test', 'production'] = Field(default='development')
	debug: bool = Field(default=False)
	host: str = Field(default='0.0.0.0')
	port: int = Field(default=8000, ge=1, le=65535)
	log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = Field(default='INFO')

	database_url: str = Field(default='')

	# Authentication
	auth_secret_key: SecretStr = Field(
		default=SecretStr(''),
		repr=False,
	)
	auth_access_token_ttl_minutes: int = Field(default=60, ge=5, le=1440)
	auth_issuer: str = Field(default='utw-api')
	auth_audience: str = Field(default='utw-users')
	auth_cookie_name: str = Field(default='utw_access_token')
	auth_cookie_path: str = Field(default='/')
	auth_cookie_domain: str | None = Field(default=None)
	auth_cookie_same_site: Literal['lax', 'strict', 'none'] = Field(default='lax')
	auth_cookie_secure: bool = Field(default=False)

	# Operator Configuration
	operator_api_key: SecretStr = Field(
		default=SecretStr(''),
		repr=False,
	)
	cors_allow_origins: str = Field(
		default='http://127.0.0.1:5173,http://localhost:5173',
	)

	@field_validator('app_name')
	@classmethod
	def validate_app_name(cls, value: str) -> str:
		cleaned = value.strip()
		if not cleaned:
			raise ValueError('app_name must not be empty')
		return cleaned

	@field_validator('host')
	@classmethod
	def validate_host(cls, value: str) -> str:
		cleaned = value.strip()
		if not cleaned:
			raise ValueError('host must not be empty')
		return cleaned

	@field_validator('log_level', mode='before')
	@classmethod
	def normalize_log_level(cls, value: str) -> str:
		if not isinstance(value, str):
			raise TypeError('log_level must be a string')
		return value.strip().upper()

	@field_validator('database_url')
	@classmethod
	def normalize_database_url(cls, value: str) -> str:
		if not isinstance(value, str):
			raise TypeError('database_url must be a string')
		return value.strip()

	@field_validator('auth_issuer', 'auth_audience', 'auth_cookie_name')
	@classmethod
	def validate_auth_text(cls, value: str) -> str:
		cleaned = value.strip()
		if not cleaned:
			raise ValueError('auth setting must not be empty')
		return cleaned

	@field_validator('auth_cookie_path')
	@classmethod
	def validate_auth_cookie_path(cls, value: str) -> str:
		cleaned = value.strip()
		if not cleaned:
			return '/'
		if not cleaned.startswith('/'):
			raise ValueError('auth_cookie_path must start with /')
		return cleaned

	@field_validator('auth_cookie_domain')
	@classmethod
	def normalize_auth_cookie_domain(cls, value: str | None) -> str | None:
		if value is None:
			return None

		cleaned = value.strip()
		return cleaned or None

	@model_validator(mode='after')
	def validate_cookie_security(self) -> 'Settings':
		if self.environment == 'production':
			if self.debug:
				raise ValueError('debug must be disabled in production')
			if not self.database_url:
				raise ValueError('database_url must be configured in production')
			if not self.auth_secret_key.get_secret_value().strip():
				raise ValueError('auth_secret_key must be configured in production')
			if not self.cors_allow_origins_list:
				raise ValueError('cors_allow_origins must be configured in production')
			for origin in self.cors_allow_origins_list:
				if origin in {'*'}:
					raise ValueError('wildcard CORS origins are not allowed in production')
				if origin.startswith('http://localhost') or origin.startswith('http://127.0.0.1'):
					raise ValueError('localhost CORS origins are not allowed in production')
				if not origin.startswith('https://'):
					raise ValueError('production CORS origins must use https://')
			if not self.auth_cookie_secure:
				raise ValueError('auth_cookie_secure must be enabled in production')

		if self.auth_cookie_same_site == 'none' and not (self.auth_cookie_secure or self.environment == 'production'):
			raise ValueError("auth_cookie_same_site='none' requires auth_cookie_secure=true or production environment")
		return self

	@field_validator('cors_allow_origins')
	@classmethod
	def normalize_cors_allow_origins(cls, value: str) -> str:
		if not isinstance(value, str):
			raise TypeError('cors_allow_origins must be a string')

		cleaned_values = [item.strip() for item in value.split(',') if item.strip()]
		return ','.join(cleaned_values)

	@property
	def reload_enabled(self) -> bool:
		return self.environment == 'development' and self.debug

	@property
	def cors_allow_origins_list(self) -> list[str]:
		"""Return the allowed CORS origins as a normalized list."""
		return [origin for origin in self.cors_allow_origins.split(',') if origin]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	"""Return a cached settings instance."""
	return Settings()
