from __future__ import annotations

from contextlib import AbstractContextManager

import pytest

from src.jobs.send_pending_daily_briefs_job_service import (
	SendPendingDailyBriefsJobAlreadyRunningError,
	run_send_pending_daily_briefs_job,
)
from src.jobs.send_pending_instant_alerts_job_service import (
	SendPendingInstantAlertsJobAlreadyRunningError,
	run_send_pending_instant_alerts_job,
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
	def __init__(self, sessions: list[FakeSession]):
		self._sessions = sessions
		self._index = 0

	def __call__(self) -> FakeSession:
		session = self._sessions[self._index]
		self._index += 1
		return session


def test_run_send_pending_daily_briefs_job_returns_success_when_lock_release_fails(
	monkeypatch: pytest.MonkeyPatch,
	caplog: pytest.LogCaptureFixture,
) -> None:
	events: list[str] = []
	lock_session = FakeSession(events=events)
	read_session = FakeSession(events=events)
	pending_session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.send_pending_daily_briefs_job_service.get_session_factory',
		lambda: FakeSessionFactory([lock_session, read_session, pending_session]),
	)
	monkeypatch.setattr(
		'src.jobs.send_pending_daily_briefs_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or True,
	)
	monkeypatch.setattr(
		'src.jobs.send_pending_daily_briefs_job_service._list_pending_daily_brief_user_ids',
		lambda session: events.append('list-users') or [],
	)
	monkeypatch.setattr(
		'src.jobs.send_pending_daily_briefs_job_service.list_pending_email_delivery_ids',
		lambda session, *, delivery_type: events.append('list-deliveries') or [],
	)
	monkeypatch.setattr(
		'src.jobs.job_lock_service.release_named_job_lock',
		lambda session, *, job_name: events.append('release') or False,
	)

	with caplog.at_level('WARNING'):
		result = run_send_pending_daily_briefs_job()

	assert result.overall_status == 'success'
	assert result.processed_user_count == 0
	assert result.sent_delivery_count == 0
	assert result.skipped_user_count == 0
	assert lock_session.rollback_calls == 0
	assert events == ['acquire', 'list-users', 'list-deliveries', 'release']
	assert 'job_lock_release_failed' in caplog.text


def test_run_send_pending_daily_briefs_job_raises_when_lock_is_held(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	events: list[str] = []
	lock_session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.send_pending_daily_briefs_job_service.get_session_factory',
		lambda: FakeSessionFactory([lock_session]),
	)
	monkeypatch.setattr(
		'src.jobs.send_pending_daily_briefs_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or False,
	)

	with pytest.raises(SendPendingDailyBriefsJobAlreadyRunningError):
		run_send_pending_daily_briefs_job()

	assert events == ['acquire']


def test_run_send_pending_instant_alerts_job_returns_success_when_lock_release_fails(
	monkeypatch: pytest.MonkeyPatch,
	caplog: pytest.LogCaptureFixture,
) -> None:
	events: list[str] = []
	lock_session = FakeSession(events=events)
	read_session = FakeSession(events=events)
	pending_session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.send_pending_instant_alerts_job_service.get_session_factory',
		lambda: FakeSessionFactory([lock_session, read_session, pending_session]),
	)
	monkeypatch.setattr(
		'src.jobs.send_pending_instant_alerts_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or True,
	)
	monkeypatch.setattr(
		'src.jobs.send_pending_instant_alerts_job_service._list_pending_instant_alert_user_ids',
		lambda session: events.append('list-users') or [],
	)
	monkeypatch.setattr(
		'src.jobs.send_pending_instant_alerts_job_service.list_pending_email_delivery_ids',
		lambda session, *, delivery_type: events.append('list-deliveries') or [],
	)
	monkeypatch.setattr(
		'src.jobs.job_lock_service.release_named_job_lock',
		lambda session, *, job_name: events.append('release') or False,
	)

	with caplog.at_level('WARNING'):
		result = run_send_pending_instant_alerts_job()

	assert result.overall_status == 'success'
	assert result.processed_user_count == 0
	assert result.sent_delivery_count == 0
	assert result.skipped_user_count == 0
	assert lock_session.rollback_calls == 0
	assert events == ['acquire', 'list-users', 'list-deliveries', 'release']
	assert 'job_lock_release_failed' in caplog.text


def test_run_send_pending_instant_alerts_job_raises_when_lock_is_held(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	events: list[str] = []
	lock_session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.send_pending_instant_alerts_job_service.get_session_factory',
		lambda: FakeSessionFactory([lock_session]),
	)
	monkeypatch.setattr(
		'src.jobs.send_pending_instant_alerts_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or False,
	)

	with pytest.raises(SendPendingInstantAlertsJobAlreadyRunningError):
		run_send_pending_instant_alerts_job()

	assert events == ['acquire']
