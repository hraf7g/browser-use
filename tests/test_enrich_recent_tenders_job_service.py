from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import UTC, datetime

import pytest

from src.ai.tender_enrichment_service import TenderEnrichmentResult
from src.jobs.enrich_recent_tenders_job_service import (
	EnrichRecentTendersJobAlreadyRunningError,
	run_enrich_recent_tenders_job,
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


def test_run_enrich_recent_tenders_job_commits_and_releases_lock(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	events: list[str] = []
	session = FakeSession(events=events)
	expected_result = TenderEnrichmentResult(
		attempted_count=3,
		enriched_count=2,
		failed_count=1,
		skipped_count=0,
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.get_session_factory',
		lambda: FakeSessionFactory(session),
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or True,
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.enrich_tenders_updated_since',
		lambda session, *, since: events.append('enrich') or expected_result,
	)
	monkeypatch.setattr(
		'src.jobs.job_lock_service.release_named_job_lock',
		lambda session, *, job_name: events.append('release') or True,
	)

	result = run_enrich_recent_tenders_job(since=datetime.now(UTC))

	assert result == expected_result
	assert session.commit_calls == 1
	assert session.rollback_calls == 0
	assert events == ['acquire', 'enrich', 'commit', 'release']


def test_run_enrich_recent_tenders_job_raises_when_lock_is_held(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	events: list[str] = []
	session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.get_session_factory',
		lambda: FakeSessionFactory(session),
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or False,
	)
	monkeypatch.setattr(
		'src.jobs.job_lock_service.release_named_job_lock',
		lambda session, *, job_name: events.append('release') or True,
	)

	with pytest.raises(EnrichRecentTendersJobAlreadyRunningError):
		run_enrich_recent_tenders_job(since=datetime.now(UTC))

	assert session.commit_calls == 0
	assert session.rollback_calls == 1
	assert events == ['acquire', 'rollback']


def test_run_enrich_recent_tenders_job_rolls_back_and_releases_lock_on_failure(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	events: list[str] = []
	session = FakeSession(events=events)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.get_session_factory',
		lambda: FakeSessionFactory(session),
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or True,
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.enrich_tenders_updated_since',
		lambda session, *, since: events.append('enrich') or (_ for _ in ()).throw(RuntimeError('bedrock unavailable')),
	)
	monkeypatch.setattr(
		'src.jobs.job_lock_service.release_named_job_lock',
		lambda session, *, job_name: events.append('release') or True,
	)

	with pytest.raises(RuntimeError, match='bedrock unavailable'):
		run_enrich_recent_tenders_job(since=datetime.now(UTC))

	assert session.commit_calls == 0
	assert session.rollback_calls == 1
	assert events == ['acquire', 'enrich', 'rollback', 'release']


def test_run_enrich_recent_tenders_job_raises_when_lock_release_fails(
	monkeypatch: pytest.MonkeyPatch,
	caplog: pytest.LogCaptureFixture,
) -> None:
	events: list[str] = []
	session = FakeSession(events=events)
	expected_result = TenderEnrichmentResult(
		attempted_count=1,
		enriched_count=1,
		failed_count=0,
		skipped_count=0,
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.get_session_factory',
		lambda: FakeSessionFactory(session),
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.acquire_named_job_lock',
		lambda session, *, job_name: events.append('acquire') or True,
	)
	monkeypatch.setattr(
		'src.jobs.enrich_recent_tenders_job_service.enrich_tenders_updated_since',
		lambda session, *, since: events.append('enrich') or expected_result,
	)
	monkeypatch.setattr(
		'src.jobs.job_lock_service.release_named_job_lock',
		lambda session, *, job_name: events.append('release') or False,
	)

	with caplog.at_level('WARNING'):
		result = run_enrich_recent_tenders_job(since=datetime.now(UTC))

	assert result == expected_result
	assert session.commit_calls == 1
	assert session.rollback_calls == 0
	assert events == ['acquire', 'enrich', 'commit', 'release']
	assert 'job_lock_release_failed' in caplog.text
