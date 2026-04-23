from __future__ import annotations

import pytest

import src.shared.config.settings as settings_module
from src.ai.factory import AIRuntimeDependencyError, build_ai_runtime
from src.shared.config.settings import Settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
	settings_module.get_settings.cache_clear()
	yield
	settings_module.get_settings.cache_clear()


def test_build_ai_runtime_returns_disabled_runtime_by_default(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.delenv('UTW_AI_PROVIDER', raising=False)
	monkeypatch.delenv('BROWSER_USE_API_KEY', raising=False)

	runtime = build_ai_runtime(Settings())

	assert runtime.provider == 'disabled'
	assert runtime.llm is None
	assert runtime.fallback_llm is None


def test_build_ai_runtime_creates_bedrock_primary_and_fallback_without_browser_use_key(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setenv('UTW_AI_PROVIDER', 'bedrock_anthropic')
	monkeypatch.setenv('UTW_AWS_REGION', 'us-east-1')
	monkeypatch.setenv('UTW_AI_MODEL', 'anthropic.claude-sonnet-4-6')
	monkeypatch.setenv('UTW_AI_FALLBACK_MODEL', 'anthropic.claude-haiku-4-5')
	monkeypatch.setenv('UTW_AI_BEDROCK_USE_AMBIENT_CREDENTIALS', 'true')
	monkeypatch.setenv('UTW_AI_MAX_TOKENS', '4096')
	monkeypatch.setenv('UTW_AI_TEMPERATURE', '0.1')
	monkeypatch.delenv('BROWSER_USE_API_KEY', raising=False)

	created: list[dict[str, object]] = []

	class FakeChatAnthropicBedrock:
		provider = 'anthropic_bedrock'

		def __init__(self, **kwargs):
			self.kwargs = kwargs
			created.append(kwargs)

	monkeypatch.setattr('src.ai.factory._validate_bedrock_runtime_dependencies', lambda: None)
	monkeypatch.setattr('src.ai.factory._get_bedrock_chat_class', lambda: FakeChatAnthropicBedrock)

	runtime = build_ai_runtime(Settings())

	assert runtime.provider == 'bedrock_anthropic'
	assert runtime.llm is not None
	assert runtime.fallback_llm is not None
	assert created == [
		{
			'model': 'anthropic.claude-sonnet-4-6',
			'aws_region': 'us-east-1',
			'aws_sso_auth': True,
			'max_tokens': 4096,
			'temperature': 0.1,
		},
		{
			'model': 'anthropic.claude-haiku-4-5',
			'aws_region': 'us-east-1',
			'aws_sso_auth': True,
			'max_tokens': 4096,
			'temperature': 0.1,
		},
	]


def test_build_ai_runtime_raises_when_bedrock_dependencies_are_missing(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setenv('UTW_AI_PROVIDER', 'bedrock_anthropic')
	monkeypatch.setenv('UTW_AWS_REGION', 'us-east-1')

	monkeypatch.setattr(
		'src.ai.factory._validate_bedrock_runtime_dependencies',
		lambda: (_ for _ in ()).throw(AIRuntimeDependencyError('missing boto3')),
	)

	with pytest.raises(AIRuntimeDependencyError, match='missing boto3'):
		build_ai_runtime(Settings())
