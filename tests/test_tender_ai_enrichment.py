from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
from uuid import uuid4

import pytest

from src.ai.control_service import AI_CONTROL_SINGLETON_ID
from src.ai.factory import AIRuntime
from src.ai.tender_enrichment_service import enrich_tenders_updated_since
from src.ai.usage_budget_service import AIDailyBudgetExceededError
from src.db.models.ai_control_state import AIControlState
from src.db.models.ai_daily_usage import AIDailyUsage
from src.db.models.tender import Tender
from src.shared.config.settings import Settings

if TYPE_CHECKING:
	from sqlalchemy.orm import Session

	from browser_use.llm.base import BaseChatModel


class _ScalarListResult:
	def __init__(self, values: Sequence[object]):
		self._values = values

	def scalars(self) -> _ScalarListResult:
		return self

	def all(self) -> list[object]:
		return list(self._values)


class FakeSession:
	def __init__(self, *, tenders: list[Tender]):
		self._tenders = tenders
		self._state: AIControlState | None = None
		self._daily_usage: dict[object, AIDailyUsage] = {}
		self.flush_calls = 0

	def get(self, model: object, identifier: object):
		if model is AIControlState and identifier == AI_CONTROL_SINGLETON_ID:
			return self._state
		if model is AIDailyUsage:
			return self._daily_usage.get(identifier)
		return None

	def add(self, instance: object) -> None:
		if isinstance(instance, AIControlState):
			self._state = instance
		if isinstance(instance, AIDailyUsage):
			self._daily_usage[instance.usage_date] = instance

	def execute(self, statement: object) -> _ScalarListResult:
		return _ScalarListResult(self._tenders)

	def flush(self) -> None:
		self.flush_calls += 1
		now = datetime.now(UTC)
		if self._state is not None and getattr(self._state, 'created_at', None) is None:
			self._state.created_at = now
			self._state.updated_at = now
		for usage in self._daily_usage.values():
			if getattr(usage, 'created_at', None) is None:
				usage.created_at = now
			usage.updated_at = now


class FakeLLM:
	provider = 'anthropic_bedrock'

	def __init__(self, *, model: str, bullets: list[str] | None = None, error: Exception | None = None):
		self.model = model
		self._bullets = bullets
		self._error = error

	async def ainvoke(self, messages, output_format=None, **kwargs):
		if self._error is not None:
			raise self._error
		assert output_format is not None
		return SimpleNamespace(
			completion=output_format(
				bullets=self._bullets
				or [
					'Public tender for technology services.',
					'Issued by a government digital authority.',
					'Closing date is explicitly provided in source fields.',
				]
			),
			usage=SimpleNamespace(
				prompt_tokens=120,
				prompt_cached_tokens=None,
				prompt_cache_creation_tokens=None,
				prompt_image_tokens=None,
				completion_tokens=80,
				total_tokens=200,
			),
		)


def _build_settings() -> Settings:
	return Settings(
		ai_provider='bedrock_anthropic',
		aws_region='us-east-1',
		ai_summary_batch_size=10,
		ai_summary_max_attempts=3,
	)


def _build_tender() -> Tender:
	now = datetime.now(UTC)
	return Tender(
		id=uuid4(),
		source_id=uuid4(),
		source_url='https://example.gov/tenders/123',
		title='Digital network security platform',
		issuing_entity='National Digital Authority',
		closing_date=now + timedelta(days=7),
		opening_date=now - timedelta(days=1),
		published_at=now - timedelta(days=2),
		category='Cybersecurity',
		industry_codes=[],
		primary_industry_code=None,
		ai_summary=None,
		ai_summary_attempt_count=0,
		ai_summary_generated_at=None,
		ai_summary_last_attempted_at=None,
		ai_summary_last_error=None,
		ai_summary_model=None,
		dedupe_key='dedupe-123',
		search_text='digital network security platform national digital authority cybersecurity',
		created_at=now - timedelta(hours=3),
		updated_at=now - timedelta(minutes=10),
	)


def test_enrich_tenders_updated_since_persists_summary_and_derived_fields(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	tender = _build_tender()
	session = FakeSession(tenders=[tender])
	fake_llm = FakeLLM(
		model='us.anthropic.claude-sonnet-4-20250514-v1:0',
		bullets=[
			'Government procurement for a digital security platform.',
			'Buyer is the National Digital Authority.',
			'Closing timeline is stated in the tender listing.',
		],
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.build_ai_runtime',
		lambda settings: AIRuntime(
			provider='bedrock_anthropic',
			llm=cast('BaseChatModel', fake_llm),
			fallback_llm=None,
		),
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.reserve_ai_budget_for_messages',
		lambda *args, **kwargs: SimpleNamespace(
			usage_date=datetime.now(UTC).date(),
			model_id='us.anthropic.claude-sonnet-4-20250514-v1:0',
			estimated_input_tokens=140,
			reserved_total_tokens=8_332,
		),
	)

	result = enrich_tenders_updated_since(
		cast('Session', session),
		since=datetime.now(UTC) - timedelta(days=1),
		settings=_build_settings(),
	)

	assert result.attempted_count == 1
	assert result.enriched_count == 1
	assert result.failed_count == 0
	assert tender.ai_summary == (
		'• Government procurement for a digital security platform.\n'
		'• Buyer is the National Digital Authority.\n'
		'• Closing timeline is stated in the tender listing.'
	)
	assert tender.ai_summary_attempt_count == 1
	assert tender.ai_summary_model == 'us.anthropic.claude-sonnet-4-20250514-v1:0'
	assert tender.ai_summary_generated_at is not None
	assert tender.ai_summary_last_error is None
	assert 'government procurement for a digital security platform' in tender.search_text
	assert 'technology' in tender.industry_codes
	assert tender.primary_industry_code == 'technology'
	assert session.flush_calls == 4


def test_enrich_tenders_updated_since_uses_fallback_llm_when_primary_fails(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	tender = _build_tender()
	session = FakeSession(tenders=[tender])
	primary_llm = FakeLLM(
		model='us.anthropic.claude-sonnet-4-20250514-v1:0',
		error=RuntimeError('primary bedrock failure'),
	)
	fallback_llm = FakeLLM(
		model='us.anthropic.claude-haiku-4-5-20251001-v1:0',
		bullets=[
			'Technology procurement for cybersecurity capabilities.',
			'Issuer is clearly identified in the source data.',
			'Timing details come from the published listing fields.',
		],
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.build_ai_runtime',
		lambda settings: AIRuntime(
			provider='bedrock_anthropic',
			llm=cast('BaseChatModel', primary_llm),
			fallback_llm=cast('BaseChatModel', fallback_llm),
		),
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.reserve_ai_budget_for_messages',
		lambda *args, **kwargs: SimpleNamespace(
			usage_date=datetime.now(UTC).date(),
			model_id='bedrock-model',
			estimated_input_tokens=140,
			reserved_total_tokens=8_332,
		),
	)

	result = enrich_tenders_updated_since(
		cast('Session', session),
		since=datetime.now(UTC) - timedelta(days=1),
		settings=_build_settings(),
	)

	assert result.enriched_count == 1
	assert tender.ai_summary_model == 'us.anthropic.claude-haiku-4-5-20251001-v1:0'
	assert tender.ai_summary_attempt_count == 1
	assert tender.ai_summary_last_error is None


def test_enrich_tenders_updated_since_records_failure_without_infinite_retry_state(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	tender = _build_tender()
	session = FakeSession(tenders=[tender])
	fake_llm = FakeLLM(
		model='us.anthropic.claude-sonnet-4-20250514-v1:0',
		error=RuntimeError('bedrock temporarily unavailable'),
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.build_ai_runtime',
		lambda settings: AIRuntime(
			provider='bedrock_anthropic',
			llm=cast('BaseChatModel', fake_llm),
			fallback_llm=None,
		),
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.reserve_ai_budget_for_messages',
		lambda *args, **kwargs: SimpleNamespace(
			usage_date=datetime.now(UTC).date(),
			model_id='us.anthropic.claude-sonnet-4-20250514-v1:0',
			estimated_input_tokens=140,
			reserved_total_tokens=8_332,
		),
	)

	result = enrich_tenders_updated_since(
		cast('Session', session),
		since=datetime.now(UTC) - timedelta(days=1),
		settings=_build_settings(),
	)

	assert result.attempted_count == 1
	assert result.enriched_count == 0
	assert result.failed_count == 1
	assert tender.ai_summary is None
	assert tender.ai_summary_attempt_count == 1
	assert tender.ai_summary_last_attempted_at is not None
	assert tender.ai_summary_last_error == 'bedrock temporarily unavailable'
	assert tender.ai_summary_generated_at is None


def test_enrich_tenders_updated_since_stops_without_consuming_attempt_when_budget_is_blocked(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	tender = _build_tender()
	session = FakeSession(tenders=[tender])
	fake_llm = FakeLLM(
		model='us.anthropic.claude-sonnet-4-20250514-v1:0',
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.build_ai_runtime',
		lambda settings: AIRuntime(
			provider='bedrock_anthropic',
			llm=cast('BaseChatModel', fake_llm),
			fallback_llm=None,
		),
	)
	monkeypatch.setattr(
		'src.ai.tender_enrichment_service.reserve_ai_budget_for_messages',
		lambda *args, **kwargs: (_ for _ in ()).throw(AIDailyBudgetExceededError('daily_reserved_token_budget_exhausted')),
	)

	result = enrich_tenders_updated_since(
		cast('Session', session),
		since=datetime.now(UTC) - timedelta(days=1),
		settings=_build_settings(),
	)

	assert result.attempted_count == 0
	assert result.enriched_count == 0
	assert result.failed_count == 0
	assert result.skipped_count == 1
	assert tender.ai_summary_attempt_count == 0
