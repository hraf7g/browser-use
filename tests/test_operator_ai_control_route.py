from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import src.shared.config.settings as settings_module
from src.api.app import create_app
from src.api.dependencies.auth import get_current_user_optional
from src.db.session import get_db_session


@pytest.fixture(autouse=True)
def clear_settings_cache():
	settings_module.get_settings.cache_clear()
	yield
	settings_module.get_settings.cache_clear()


def _set_operator_env(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv('UTW_OPERATOR_API_KEY', 'operator-secret-key')


def test_get_operator_ai_control_returns_service_response(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_set_operator_env(monkeypatch)
	app = create_app()

	def override_session():
		return object()

	monkeypatch.setattr(
		'src.api.routes.operator_status.build_ai_control_response',
		lambda session: SimpleNamespace(
			ai_enrichment_enabled=True,
			emergency_stop_enabled=False,
			emergency_stop_reason=None,
			max_enrichment_batch_size_override=None,
			max_daily_requests_override=None,
			max_daily_reserved_tokens_override=None,
			effective_ai_provider='bedrock_anthropic',
			effective_ai_enrichment_enabled=True,
			effective_enrichment_batch_size=25,
			effective_daily_request_budget=100,
			effective_daily_reserved_token_budget=100_000,
			today_usage_date=datetime.now(UTC).date(),
			today_request_count=4,
			today_blocked_request_count=0,
			today_throttled_request_count=0,
			today_provider_error_count=0,
			today_estimated_input_tokens=600,
			today_reserved_total_tokens=5_000,
			today_actual_prompt_tokens=400,
			today_actual_completion_tokens=120,
			today_actual_total_tokens=520,
			budget_exhausted=False,
			budget_exhausted_reason=None,
			created_at=datetime.now(UTC),
			updated_at=datetime.now(UTC),
		),
	)
	app.dependency_overrides[get_db_session] = override_session

	client = TestClient(app)
	response = client.get(
		'/operator/ai-control',
		headers={'X-Operator-Key': 'operator-secret-key'},
	)

	assert response.status_code == 200
	assert response.json()['effective_ai_provider'] == 'bedrock_anthropic'
	assert response.json()['effective_ai_enrichment_enabled'] is True
	assert response.json()['today_request_count'] == 4


def test_put_operator_ai_control_persists_and_commits(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_set_operator_env(monkeypatch)
	app = create_app()
	calls: list[object] = []

	class FakeSession:
		def commit(self) -> None:
			calls.append('commit')

	def override_session():
		return FakeSession()

	monkeypatch.setattr(
		'src.api.routes.operator_status.update_ai_control_state',
		lambda session, *, payload: calls.append(payload)
		or SimpleNamespace(
			ai_enrichment_enabled=False,
			emergency_stop_enabled=True,
			emergency_stop_reason='halt',
			max_enrichment_batch_size_override=3,
			max_daily_requests_override=9,
			max_daily_reserved_tokens_override=20_000,
			effective_ai_provider='bedrock_anthropic',
			effective_ai_enrichment_enabled=False,
			effective_enrichment_batch_size=0,
			effective_daily_request_budget=9,
			effective_daily_reserved_token_budget=20_000,
			today_usage_date=datetime.now(UTC).date(),
			today_request_count=9,
			today_blocked_request_count=1,
			today_throttled_request_count=0,
			today_provider_error_count=0,
			today_estimated_input_tokens=1_100,
			today_reserved_total_tokens=20_000,
			today_actual_prompt_tokens=800,
			today_actual_completion_tokens=200,
			today_actual_total_tokens=1_000,
			budget_exhausted=True,
			budget_exhausted_reason='daily_request_budget_exhausted',
			created_at=datetime.now(UTC),
			updated_at=datetime.now(UTC),
		),
	)
	app.dependency_overrides[get_db_session] = override_session

	client = TestClient(app)
	response = client.put(
		'/operator/ai-control',
		headers={'X-Operator-Key': 'operator-secret-key'},
		json={
			'ai_enrichment_enabled': False,
			'emergency_stop_enabled': True,
			'emergency_stop_reason': 'halt',
			'max_enrichment_batch_size_override': 3,
			'max_daily_requests_override': 9,
			'max_daily_reserved_tokens_override': 20_000,
		},
	)

	assert response.status_code == 200
	assert response.json()['emergency_stop_enabled'] is True
	assert response.json()['effective_ai_enrichment_enabled'] is False
	assert response.json()['budget_exhausted'] is True
	assert calls[-1] == 'commit'


def test_get_operator_ai_control_allows_operator_session_without_api_key(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	app = create_app()

	def override_session():
		return object()

	monkeypatch.setattr(
		'src.api.routes.operator_status.build_ai_control_response',
		lambda session: SimpleNamespace(
			ai_enrichment_enabled=True,
			emergency_stop_enabled=False,
			emergency_stop_reason=None,
			max_enrichment_batch_size_override=None,
			max_daily_requests_override=None,
			max_daily_reserved_tokens_override=None,
			effective_ai_provider='bedrock_anthropic',
			effective_ai_enrichment_enabled=True,
			effective_enrichment_batch_size=25,
			effective_daily_request_budget=100,
			effective_daily_reserved_token_budget=100_000,
			today_usage_date=datetime.now(UTC).date(),
			today_request_count=4,
			today_blocked_request_count=0,
			today_throttled_request_count=0,
			today_provider_error_count=0,
			today_estimated_input_tokens=600,
			today_reserved_total_tokens=5_000,
			today_actual_prompt_tokens=400,
			today_actual_completion_tokens=120,
			today_actual_total_tokens=520,
			budget_exhausted=False,
			budget_exhausted_reason=None,
			created_at=datetime.now(UTC),
			updated_at=datetime.now(UTC),
		),
	)
	app.dependency_overrides[get_db_session] = override_session
	app.dependency_overrides[get_current_user_optional] = lambda: SimpleNamespace(
		id='00000000-0000-0000-0000-000000000901',
		email='operator@example.com',
		is_active=True,
		is_operator=True,
	)

	client = TestClient(app)
	response = client.get('/operator/ai-control')

	assert response.status_code == 200
	assert response.json()['effective_ai_provider'] == 'bedrock_anthropic'


def test_get_operator_ai_control_rejects_non_operator_session_without_api_key() -> None:
	app = create_app()
	app.dependency_overrides[get_db_session] = lambda: object()
	app.dependency_overrides[get_current_user_optional] = lambda: SimpleNamespace(
		id='00000000-0000-0000-0000-000000000902',
		email='user@example.com',
		is_active=True,
		is_operator=False,
	)

	client = TestClient(app, raise_server_exceptions=False)
	response = client.get('/operator/ai-control')

	assert response.status_code == 403
	assert response.json() == {'detail': 'operator role required'}
