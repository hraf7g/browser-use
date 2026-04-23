from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.shared.config.settings import Settings, get_settings

if TYPE_CHECKING:
	from browser_use.llm.base import BaseChatModel


class AIRuntimeDependencyError(RuntimeError):
	"""Raised when the configured AI runtime cannot be created safely."""


@dataclass(frozen=True)
class AIRuntime:
	"""Resolved application AI runtime contract."""

	provider: str
	llm: BaseChatModel | None
	fallback_llm: BaseChatModel | None


def build_ai_runtime(settings: Settings | None = None) -> AIRuntime:
	"""
	Build the application-owned AI runtime.

	Notes:
		- Browser Use Cloud is intentionally not a supported provider here.
		- When Bedrock is enabled we validate the runtime contract eagerly.
	"""
	cfg = settings or get_settings()

	if cfg.ai_provider == 'disabled':
		return AIRuntime(provider='disabled', llm=None, fallback_llm=None)

	if cfg.ai_provider != 'bedrock_anthropic':
		raise AIRuntimeDependencyError(f'unsupported ai_provider: {cfg.ai_provider!r}')

	_validate_bedrock_runtime_dependencies()
	llm = _build_bedrock_anthropic_llm(
		model_id=cfg.ai_model,
		settings=cfg,
	)
	fallback_llm = None
	if cfg.ai_fallback_model and cfg.ai_fallback_model != cfg.ai_model:
		fallback_llm = _build_bedrock_anthropic_llm(
			model_id=cfg.ai_fallback_model,
			settings=cfg,
		)

	return AIRuntime(
		provider=cfg.ai_provider,
		llm=llm,
		fallback_llm=fallback_llm,
	)


def _build_bedrock_anthropic_llm(*, model_id: str, settings: Settings):
	"""
	Create one Bedrock Anthropic chat model.

	We intentionally use the upstream `aws_sso_auth` switch to activate the default
	AWS credential chain, which includes ECS task roles and EC2 instance profiles.
	"""
	chat_class = _get_bedrock_chat_class()
	return chat_class(
		model=model_id,
		aws_region=settings.aws_region,
		aws_sso_auth=settings.ai_bedrock_use_ambient_credentials,
		max_tokens=settings.ai_max_tokens,
		temperature=settings.ai_temperature,
	)


def _get_bedrock_chat_class():
	try:
		from browser_use.llm.aws import ChatAnthropicBedrock
	except ImportError as exc:
		raise AIRuntimeDependencyError(
			'Amazon Bedrock AI runtime is unavailable. Ensure browser-use AWS support is present.'
		) from exc

	return ChatAnthropicBedrock


def _validate_bedrock_runtime_dependencies() -> None:
	try:
		import boto3  # noqa: F401
	except ImportError as exc:
		raise AIRuntimeDependencyError(
			'Amazon Bedrock AI runtime requires boto3. Install AWS dependencies with `uv sync --extra aws`.'
		) from exc
