from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import UTC, datetime

import pytest

from src.jobs.match_recent_tenders_job_service import (
	MatchRecentTendersJobAlreadyRunningError,
	run_match_recent_tenders_job,
)


class FakeSession(AbstractContextManager['FakeSession']):
	def __init__(self, *, events: list[str]):
		self.events = events
		self.commit_calls = 0
		self.rollback_calls = 0

	def commit(self) -> None:
		self.commit_calls += 1
		self.events.append('commit')

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


def test_run_match_recent_tenders_job_returns_result_when_lock_release_fails(
	monkeypatch: pytest.MonkeyPatch,
	caplog: pytest.LogCaptureFixture,
) -> None:
	events: list[str] = []
	session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.match_recent_tenders_job_service.get_session_factory',
		lambda: FakeSessionFactory(session),
	)
	monkeypatch.setattr(
		'src.jobs.match_recent_tenders_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or True,
	)
	monkeypatch.setattr(
		'src.jobs.match_recent_tenders_job_service.match_tenders_updated_since',
		lambda session, *, since: events.append('match') or 3,
	)
	monkeypatch.setattr(
		'src.jobs.job_lock_service.release_named_job_lock',
		lambda session, *, job_name: events.append('release') or False,
	)

	with caplog.at_level('WARNING'):
		result = run_match_recent_tenders_job(since=datetime.now(UTC))

	assert result == 3
	assert session.commit_calls == 1
	assert session.rollback_calls == 0
	assert events == ['acquire', 'match', 'commit', 'release']
	assert 'job_lock_release_failed' in caplog.text


def test_run_match_recent_tenders_job_raises_when_lock_is_held(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	events: list[str] = []
	session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.match_recent_tenders_job_service.get_session_factory',
		lambda: FakeSessionFactory(session),
	)
	monkeypatch.setattr(
		'src.jobs.match_recent_tenders_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or False,
	)

	with pytest.raises(MatchRecentTendersJobAlreadyRunningError):
		run_match_recent_tenders_job(since=datetime.now(UTC))

	assert session.commit_calls == 0
	assert session.rollback_calls == 1
	assert events == ['acquire', 'rollback']
