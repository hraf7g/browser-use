from __future__ import annotations

import pytest

from browser_use.agent.service import Agent
from browser_use.llm.models import get_llm_by_name


class FakeBedrockLLM:
	provider = 'anthropic_bedrock'

	def __init__(self, **kwargs):
		self.kwargs = kwargs
		self.model = kwargs['model']

	async def ainvoke(self, messages, output_format=None, **kwargs):
		raise NotImplementedError


@pytest.fixture(autouse=True)
def clear_relevant_env(monkeypatch: pytest.MonkeyPatch) -> None:
	for name in [
		'AWS_REGION',
		'AWS_DEFAULT_REGION',
		'BROWSER_USE_AWS_REGION',
		'BROWSER_USE_API_KEY',
		'BROWSER_USE_REQUIRE_EXPLICIT_LLM',
		'DEFAULT_LLM',
		'UTW_AWS_REGION',
	]:
		monkeypatch.delenv(name, raising=False)


def test_get_llm_by_name_supports_exact_bedrock_anthropic_model_ids(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setenv('AWS_REGION', 'us-east-1')
	monkeypatch.setattr('browser_use.llm.models.AWS_AVAILABLE', True)
	monkeypatch.setattr('browser_use.llm.models.ChatAnthropicBedrock', FakeBedrockLLM)

	llm = get_llm_by_name('bedrock_anthropic:us.anthropic.claude-sonnet-4-20250514-v1:0')

	assert isinstance(llm, FakeBedrockLLM)
	assert llm.kwargs == {
		'model': 'us.anthropic.claude-sonnet-4-20250514-v1:0',
		'aws_region': 'us-east-1',
	}


def test_agent_requires_explicit_llm_when_strict_mode_enabled(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setenv('BROWSER_USE_REQUIRE_EXPLICIT_LLM', 'true')

	with pytest.raises(ValueError, match='Implicit ChatBrowserUse\\(\\) fallback is disabled'):
		Agent(task='Test task')


def test_agent_uses_bedrock_default_llm_without_browser_use_key(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setenv('DEFAULT_LLM', 'bedrock_anthropic:us.anthropic.claude-sonnet-4-20250514-v1:0')
	monkeypatch.setenv('AWS_REGION', 'us-east-1')
	monkeypatch.setattr('browser_use.llm.models.AWS_AVAILABLE', True)
	monkeypatch.setattr('browser_use.llm.models.ChatAnthropicBedrock', FakeBedrockLLM)

	agent = Agent(task='Test task')

	assert isinstance(agent.llm, FakeBedrockLLM)
	assert agent.llm.kwargs == {
		'model': 'us.anthropic.claude-sonnet-4-20250514-v1:0',
		'aws_region': 'us-east-1',
	}
