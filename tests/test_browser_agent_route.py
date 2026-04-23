from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.dependencies.auth import get_current_user
from src.db.session import get_db_session


def _fake_user():
	return SimpleNamespace(
		id=UUID('00000000-0000-0000-0000-000000000501'),
		email='agent-user@example.com',
		is_active=True,
		is_operator=False,
	)


def test_post_browser_agent_run_queues_and_commits(monkeypatch: pytest.MonkeyPatch) -> None:
	app = create_app()
	calls: list[object] = []

	class FakeSession:
		def commit(self) -> None:
			calls.append('commit')

		def rollback(self) -> None:
			calls.append('rollback')

	def override_session():
		return FakeSession()

	app.dependency_overrides[get_db_session] = override_session
	app.dependency_overrides[get_current_user] = _fake_user
	monkeypatch.setattr(
		'src.api.routes.browser_agent_runs.queue_browser_agent_run',
		lambda session, *, user, request: SimpleNamespace(
			id='00000000-0000-0000-0000-000000000601',
			user_id=user.id,
			status='queued',
			task_prompt=request.task_prompt,
			start_url=None,
			allowed_domains=None,
			max_steps=25,
			step_timeout_seconds=180,
			llm_timeout_seconds=90,
			queued_at='2026-04-20T12:00:00Z',
			started_at=None,
			finished_at=None,
			cancel_requested_at=None,
			last_heartbeat_at=None,
			error_message=None,
			final_result_text=None,
			llm_provider='bedrock_anthropic',
			llm_model='anthropic.claude-sonnet-4-6',
			created_at='2026-04-20T12:00:00Z',
			updated_at='2026-04-20T12:00:00Z',
		),
	)

	client = TestClient(app)
	response = client.post(
		'/browser-agent-runs',
		json={'task_prompt': 'Visit the portal and summarize the first visible tender card.'},
	)

	assert response.status_code == 201
	assert response.json()['status'] == 'queued'
	assert calls[-1] == 'commit'


def test_post_browser_agent_run_cancel_returns_service_response(monkeypatch: pytest.MonkeyPatch) -> None:
	app = create_app()

	class FakeSession:
		def commit(self) -> None:
			return None

		def rollback(self) -> None:
			return None

	def override_session():
		return FakeSession()

	app.dependency_overrides[get_db_session] = override_session
	app.dependency_overrides[get_current_user] = _fake_user
	monkeypatch.setattr(
		'src.api.routes.browser_agent_runs.request_browser_agent_run_cancellation',
		lambda session, *, user_id, run_id: SimpleNamespace(
			run=SimpleNamespace(
				id=run_id,
				user_id=user_id,
				status='cancelling',
				task_prompt='prompt',
				start_url=None,
				allowed_domains=None,
				max_steps=25,
				step_timeout_seconds=180,
				llm_timeout_seconds=90,
				queued_at='2026-04-20T12:00:00Z',
				started_at='2026-04-20T12:01:00Z',
				finished_at=None,
				cancel_requested_at='2026-04-20T12:02:00Z',
				last_heartbeat_at='2026-04-20T12:02:00Z',
				error_message=None,
				final_result_text=None,
				llm_provider='bedrock_anthropic',
				llm_model='anthropic.claude-sonnet-4-6',
				created_at='2026-04-20T12:00:00Z',
				updated_at='2026-04-20T12:02:00Z',
			),
			cancelled_immediately=False,
		),
	)

	client = TestClient(app)
	response = client.post('/browser-agent-runs/00000000-0000-0000-0000-000000000777/cancel')

	assert response.status_code == 200
	assert response.json()['cancelled_immediately'] is False
	assert response.json()['run']['status'] == 'cancelling'
