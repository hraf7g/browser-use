from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import Table

from src.browser_agent.service import (
	BrowserAgentAdmissionError,
	_claim_next_browser_agent_run_with_lock,
	claim_next_browser_agent_run,
	fail_stale_browser_agent_runs,
	list_browser_agent_runs_for_user,
	queue_browser_agent_run,
	request_browser_agent_run_cancellation,
	run_browser_agent_worker_once,
)
from src.db.models.browser_agent_run import BrowserAgentRun
from src.db.models.user import User
from src.shared.config.settings import Settings
from src.shared.schemas.browser_agent import BrowserAgentRunCreateRequest


def _build_session() -> Session:
	engine = create_engine(
		'sqlite://',
		connect_args={'check_same_thread': False},
		poolclass=StaticPool,
	)
	cast(Table, User.__table__).create(engine)
	cast(Table, BrowserAgentRun.__table__).create(engine)
	return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()


def _build_settings() -> Settings:
	return Settings(
		ai_provider='bedrock_anthropic',
		aws_region='us-east-1',
		ai_daily_request_budget=500,
		ai_daily_reserved_token_budget=200000,
		browser_agent_enabled=True,
		browser_agent_default_max_steps=25,
		browser_agent_step_timeout_seconds=180,
		browser_agent_llm_timeout_seconds=90,
		browser_agent_max_concurrent_runs_per_user=1,
		browser_agent_max_queued_runs_per_user=2,
		browser_agent_max_global_running_runs=3,
	)


def _create_user(session: Session, *, email: str = 'user@example.com') -> User:
	user = User(email=email, password_hash='hashed-password', is_active=True, is_operator=False)
	session.add(user)
	session.commit()
	return user


def test_queue_browser_agent_run_enforces_per_user_queue_limit() -> None:
	session = _build_session()
	user = _create_user(session)
	settings = _build_settings()

	request = BrowserAgentRunCreateRequest(task_prompt='Browse the procurement portal and summarize the top result.')
	queue_browser_agent_run(session, user=user, request=request, settings=settings)
	queue_browser_agent_run(session, user=user, request=request, settings=settings)

	with pytest.raises(BrowserAgentAdmissionError):
		queue_browser_agent_run(session, user=user, request=request, settings=settings)


def test_cancel_queued_browser_agent_run_marks_terminal_status() -> None:
	session = _build_session()
	user = _create_user(session)
	settings = _build_settings()

	run = queue_browser_agent_run(
		session,
		user=user,
		request=BrowserAgentRunCreateRequest(task_prompt='Open the source and capture the first tender title.'),
		settings=settings,
	)
	session.commit()

	response = request_browser_agent_run_cancellation(session, user_id=user.id, run_id=run.id)

	assert response.cancelled_immediately is True
	assert response.run.status == 'cancelled'
	assert response.run.finished_at is not None


def test_claim_next_browser_agent_run_skips_user_over_concurrency_limit() -> None:
	session = _build_session()
	user = _create_user(session)
	settings = _build_settings()
	now = datetime.now(UTC)
	session.add(
		BrowserAgentRun(
			user_id=user.id,
			status='running',
			task_prompt='already running',
			start_url=None,
			allowed_domains=None,
			max_steps=25,
			step_timeout_seconds=180,
			llm_timeout_seconds=90,
			queued_at=now,
			started_at=now,
			llm_provider='bedrock_anthropic',
			llm_model='anthropic.claude-sonnet-4-6',
		)
	)
	session.add(
		BrowserAgentRun(
			user_id=user.id,
			status='queued',
			task_prompt='queued',
			start_url=None,
			allowed_domains=None,
			max_steps=25,
			step_timeout_seconds=180,
			llm_timeout_seconds=90,
			queued_at=now,
			llm_provider='bedrock_anthropic',
			llm_model='anthropic.claude-sonnet-4-6',
		)
	)
	session.commit()

	assert claim_next_browser_agent_run(session, settings=settings) is None


def test_run_browser_agent_worker_once_completes_claimed_run(monkeypatch: pytest.MonkeyPatch) -> None:
	session = _build_session()
	user = _create_user(session)
	settings = _build_settings()
	queue_browser_agent_run(
		session,
		user=user,
		request=BrowserAgentRunCreateRequest(task_prompt='Visit the site and report the first visible heading.'),
		settings=settings,
	)
	session.commit()

	factory = sessionmaker(bind=session.get_bind(), autoflush=False, autocommit=False, expire_on_commit=False)
	monkeypatch.setattr('src.browser_agent.service.get_session_factory', lambda: factory)
	monkeypatch.setattr(
		'src.browser_agent.service.build_ai_runtime',
		lambda settings: SimpleNamespace(
			llm=SimpleNamespace(provider='bedrock'),
			fallback_llm=None,
		),
	)

	class FakeHistory:
		def final_result(self) -> str:
			return 'Top heading: Procurement Opportunities'

	class FakeBrowserSession:
		def __init__(self, *args, **kwargs):
			pass

		async def stop(self) -> None:
			return None

	class FakeAgent:
		def __init__(self, *args, **kwargs):
			pass

		async def run(self, max_steps: int):
			return FakeHistory()

	monkeypatch.setattr(
		'src.browser_agent.service._get_browser_use_runtime_classes',
		lambda: (FakeAgent, FakeBrowserSession),
	)

	result = run_browser_agent_worker_once(settings=settings)

	assert result is not None
	assert result.status == 'completed'
	assert result.final_result_text == 'Top heading: Procurement Opportunities'


def test_fail_stale_browser_agent_runs_marks_expired_running_run_failed() -> None:
	session = _build_session()
	user = _create_user(session)
	settings = _build_settings()
	stale_started_at = datetime.now(UTC)
	session.add(
		BrowserAgentRun(
			user_id=user.id,
			status='running',
			task_prompt='stale run',
			start_url=None,
			allowed_domains=None,
			max_steps=25,
			step_timeout_seconds=180,
			llm_timeout_seconds=90,
			queued_at=stale_started_at,
			started_at=stale_started_at,
			last_heartbeat_at=stale_started_at,
			llm_provider='bedrock_anthropic',
			llm_model='anthropic.claude-sonnet-4-6',
		)
	)
	session.commit()
	effective_now = stale_started_at + timedelta(seconds=2)

	stale_count = fail_stale_browser_agent_runs(
		session,
		settings=settings.model_copy(update={'browser_agent_worker_stale_heartbeat_seconds': 1}),
		now=effective_now,
	)
	session.commit()

	run = session.execute(select(BrowserAgentRun)).scalar_one()
	assert stale_count == 1
	assert run.status == 'failed'
	assert run.error_message == 'browser agent worker heartbeat expired'
	assert run.finished_at == effective_now.replace(tzinfo=None)


def test_list_browser_agent_runs_for_user_reports_counts() -> None:
	session = _build_session()
	user = _create_user(session)
	settings = _build_settings()
	request = BrowserAgentRunCreateRequest(task_prompt='Collect the first tender title from the target site.')
	queue_browser_agent_run(session, user=user, request=request, settings=settings)
	session.commit()

	response = list_browser_agent_runs_for_user(session, user_id=user.id, settings=settings)

	assert len(response.items) == 1
	assert response.current_user_queued_count == 1
	assert response.current_user_running_count == 0


def test_claim_next_browser_agent_run_with_lock_returns_none_when_lock_is_held(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	session = _build_session()
	settings = _build_settings()

	monkeypatch.setattr('src.browser_agent.service._should_use_worker_claim_lock', lambda session: True)
	monkeypatch.setattr('src.browser_agent.service.acquire_named_job_lock', lambda session, *, job_name: False)

	assert _claim_next_browser_agent_run_with_lock(session, settings=settings) is None


def test_claim_next_browser_agent_run_with_lock_serializes_claim_and_releases_lock(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	session = _build_session()
	settings = _build_settings()
	lock_calls: list[str] = []
	expected_claim = SimpleNamespace(run_id='claim-id')

	monkeypatch.setattr('src.browser_agent.service._should_use_worker_claim_lock', lambda session: True)
	monkeypatch.setattr(
		'src.browser_agent.service.acquire_named_job_lock',
		lambda session, *, job_name: lock_calls.append(f'acquire:{job_name}') or True,
	)
	monkeypatch.setattr(
		'src.browser_agent.service.release_named_job_lock',
		lambda session, *, job_name: lock_calls.append(f'release:{job_name}') or True,
	)
	monkeypatch.setattr(
		'src.browser_agent.service.claim_next_browser_agent_run',
		lambda session, *, settings: lock_calls.append('claim') or expected_claim,
	)

	result = _claim_next_browser_agent_run_with_lock(session, settings=settings)

	assert result is expected_claim
	assert lock_calls == [
		'acquire:utw:browser_agent_worker',
		'claim',
		'release:utw:browser_agent_worker',
	]
