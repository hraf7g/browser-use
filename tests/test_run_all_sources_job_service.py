from __future__ import annotations

from contextlib import AbstractContextManager
from types import SimpleNamespace

import pytest

from src.jobs.run_all_sources_job_service import (
	AllSourcesJobAlreadyRunningError,
	run_all_sources_job,
)


class FakeSession(AbstractContextManager['FakeSession']):
	def __init__(self, *, events: list[str]):
		self.events = events
		self.rollback_calls = 0

	def rollback(self) -> None:
		self.rollback_calls += 1
		self.events.append('rollback')

	def __exit__(self, exc_type, exc, tb) -> bool:
		return False


class FakeSessionFactory:
	def __init__(self, session: FakeSession):
		self._session = session

	def __call__(self) -> FakeSession:
		return self._session


def test_run_all_sources_job_returns_result_when_lock_release_raises_after_success(
	monkeypatch: pytest.MonkeyPatch,
	caplog: pytest.LogCaptureFixture,
) -> None:
	events: list[str] = []
	session = FakeSession(events=events)
	expected_result = SimpleNamespace(overall_status='success', total_sources=6, results=[])
	monkeypatch.setattr(
		'src.jobs.run_all_sources_job_service.get_session_factory',
		lambda: FakeSessionFactory(session),
	)
	monkeypatch.setattr(
		'src.jobs.run_all_sources_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or True,
	)
	monkeypatch.setattr(
		'src.jobs.run_all_sources_job_service.run_all_supported_sources_with_isolated_transactions',
		lambda *, session_factory: events.append('run') or expected_result,
	)
	monkeypatch.setattr(
		'src.jobs.job_lock_service.release_named_job_lock',
		lambda session, *, job_name: events.append('release') or (_ for _ in ()).throw(RuntimeError('connection gone')),
	)

	with caplog.at_level('ERROR'):
		result = run_all_sources_job()

	assert result is expected_result
	assert session.rollback_calls == 0
	assert events == ['acquire', 'run', 'release']
	assert 'job_lock_release_failed' in caplog.text


def test_run_all_sources_job_raises_when_lock_is_held(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	events: list[str] = []
	session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.run_all_sources_job_service.get_session_factory',
		lambda: FakeSessionFactory(session),
	)
	monkeypatch.setattr(
		'src.jobs.run_all_sources_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or False,
	)

	with pytest.raises(AllSourcesJobAlreadyRunningError):
		run_all_sources_job()

	assert session.rollback_calls == 1
	assert events == ['acquire', 'rollback']
