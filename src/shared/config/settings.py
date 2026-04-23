from __future__ import annotations

from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_origin(value: str, *, field_name: str) -> str:
	parsed = urlparse(value)
	if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
		raise ValueError(f'{field_name} must contain absolute http(s) origins')
	if parsed.params or parsed.query or parsed.fragment:
		raise ValueError(f'{field_name} must not include params, query strings, or fragments')
	if parsed.path not in {'', '/'}:
		raise ValueError(f'{field_name} must not include paths')
	return f'{parsed.scheme}://{parsed.netloc}'


def _normalize_absolute_url(value: str, *, field_name: str) -> str:
	parsed = urlparse(value)
	if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
		raise ValueError(f'{field_name} must be an absolute http(s) URL')
	if parsed.params or parsed.query or parsed.fragment:
		raise ValueError(f'{field_name} must not include params, query strings, or fragments')
	normalized_path = parsed.path.rstrip('/')
	if normalized_path in {'', '/'}:
		return f'{parsed.scheme}://{parsed.netloc}'
	return f'{parsed.scheme}://{parsed.netloc}{normalized_path}'


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
	password_reset_token_ttl_minutes: int = Field(default=60, ge=5, le=1440)
	frontend_base_url: str = Field(default='http://127.0.0.1:3000')

	# Operator Configuration
	operator_api_key: SecretStr = Field(
		default=SecretStr(''),
		repr=False,
	)
	cors_allow_origins: str = Field(
		default='http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:5173,http://localhost:5173',
	)

	# Email
	email_delivery_backend: Literal['dev_outbox', 'ses'] = Field(default='dev_outbox')
	email_sender: str = Field(default='')
	email_reply_to: str | None = Field(default=None)
	email_ses_configuration_set: str | None = Field(default=None)
	email_ses_from_arn: str | None = Field(default=None)
	aws_region: str = Field(default='')

	# AI
	ai_provider: Literal['disabled', 'bedrock_anthropic'] = Field(default='disabled')
	ai_model: str = Field(default='anthropic.claude-sonnet-4-6')
	ai_fallback_model: str | None = Field(default='anthropic.claude-haiku-4-5')
	ai_bedrock_use_ambient_credentials: bool = Field(default=True)
	ai_max_tokens: int = Field(default=8192, ge=256, le=65536)
	ai_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
	ai_summary_batch_size: int = Field(default=25, ge=1, le=200)
	ai_summary_max_attempts: int = Field(default=3, ge=1, le=10)
	ai_daily_request_budget: int | None = Field(default=None, ge=1, le=1_000_000)
	ai_daily_reserved_token_budget: int | None = Field(default=None, ge=1, le=100_000_000)
	browser_agent_enabled: bool = Field(default=True)
	browser_agent_default_max_steps: int = Field(default=25, ge=5, le=100)
	browser_agent_step_timeout_seconds: int = Field(default=180, ge=30, le=600)
	browser_agent_llm_timeout_seconds: int = Field(default=90, ge=15, le=300)
	browser_agent_max_concurrent_runs_per_user: int = Field(default=1, ge=1, le=10)
	browser_agent_max_queued_runs_per_user: int = Field(default=3, ge=1, le=100)
	browser_agent_max_global_running_runs: int = Field(default=3, ge=1, le=100)
	browser_agent_worker_poll_seconds: int = Field(default=10, ge=1, le=300)
	browser_agent_worker_stale_heartbeat_seconds: int = Field(default=900, ge=60, le=86400)

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

	@field_validator('email_sender')
	@classmethod
	def validate_email_sender(cls, value: str) -> str:
		cleaned = value.strip().lower()
		if cleaned and '@' not in cleaned:
			raise ValueError('email_sender must be a valid email address')
		return cleaned

	@field_validator('ai_model')
	@classmethod
	def validate_ai_model(cls, value: str) -> str:
		cleaned = value.strip()
		if not cleaned:
			raise ValueError('ai_model must not be empty')
		return cleaned

	@field_validator('ai_fallback_model')
	@classmethod
	def normalize_ai_fallback_model(cls, value: str | None) -> str | None:
		if value is None:
			return None
		cleaned = value.strip()
		return cleaned or None

	@field_validator('email_reply_to')
	@classmethod
	def normalize_email_reply_to(cls, value: str | None) -> str | None:
		if value is None:
			return None

		cleaned = value.strip().lower()
		if not cleaned:
			return None
		if '@' not in cleaned:
			raise ValueError('email_reply_to must be a valid email address')
		return cleaned

	@field_validator('email_ses_configuration_set', 'email_ses_from_arn', 'aws_region')
	@classmethod
	def normalize_optional_text(cls, value: str | None) -> str | None:
		if value is None:
			return None
		return value.strip()

	@field_validator('frontend_base_url')
	@classmethod
	def validate_frontend_base_url(cls, value: str) -> str:
		cleaned = value.strip()
		if not cleaned:
			raise ValueError('frontend_base_url must not be empty')
		return _normalize_absolute_url(cleaned, field_name='frontend_base_url')

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
	def validate_cookie_security(self) -> Settings:
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
			if not self.frontend_base_url.startswith('https://'):
				raise ValueError('frontend_base_url must use https:// in production')
			if self.frontend_origin not in self.cors_allow_origins_list:
				raise ValueError('cors_allow_origins must include the frontend origin in production')
			if not self.auth_cookie_secure:
				raise ValueError('auth_cookie_secure must be enabled in production')
			if self.email_delivery_backend == 'dev_outbox':
				raise ValueError("email_delivery_backend must not use 'dev_outbox' in production")
			if not self.email_sender:
				raise ValueError('email_sender must be configured in production')
			if self.email_delivery_backend == 'ses' and not self.aws_region:
				raise ValueError('aws_region must be configured when email_delivery_backend=ses in production')
			if self.ai_provider == 'bedrock_anthropic' and not self.aws_region:
				raise ValueError('aws_region must be configured when ai_provider=bedrock_anthropic in production')

		if self.ai_provider == 'bedrock_anthropic':
			if not self.aws_region:
				raise ValueError('aws_region must be configured when ai_provider=bedrock_anthropic')
			if not self.ai_model:
				raise ValueError('ai_model must be configured when ai_provider=bedrock_anthropic')
			if self.environment == 'production':
				if self.ai_daily_request_budget is None:
					raise ValueError(
						'ai_daily_request_budget must be configured when ai_provider=bedrock_anthropic in production'
					)
				if self.ai_daily_reserved_token_budget is None:
					raise ValueError(
						'ai_daily_reserved_token_budget must be configured when ai_provider=bedrock_anthropic in production'
					)
			if self.ai_daily_reserved_token_budget is not None and self.ai_max_tokens > self.ai_daily_reserved_token_budget:
				raise ValueError('ai_max_tokens must not exceed ai_daily_reserved_token_budget')
		if self.browser_agent_max_concurrent_runs_per_user > self.browser_agent_max_global_running_runs:
			raise ValueError('browser_agent_max_concurrent_runs_per_user must not exceed browser_agent_max_global_running_runs')

		if self.auth_cookie_same_site == 'none' and not (self.auth_cookie_secure or self.environment == 'production'):
			raise ValueError("auth_cookie_same_site='none' requires auth_cookie_secure=true or production environment")
		return self

	@field_validator('cors_allow_origins')
	@classmethod
	def normalize_cors_allow_origins(cls, value: str) -> str:
		if not isinstance(value, str):
			raise TypeError('cors_allow_origins must be a string')

		cleaned_values = [
			_normalize_origin(item.strip(), field_name='cors_allow_origins') for item in value.split(',') if item.strip()
		]
		return ','.join(cleaned_values)

	@property
	def reload_enabled(self) -> bool:
		return self.environment == 'development' and self.debug

	@property
	def cors_allow_origins_list(self) -> list[str]:
		"""Return the allowed CORS origins as a normalized list."""
		return [origin for origin in self.cors_allow_origins.split(',') if origin]

	@property
	def frontend_origin(self) -> str:
		parsed = urlparse(self.frontend_base_url)
		return f'{parsed.scheme}://{parsed.netloc}'


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	"""Return a cached settings instance."""
	return Settings()
