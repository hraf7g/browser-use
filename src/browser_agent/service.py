from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from src.ai.factory import build_ai_runtime
from src.db.models.browser_agent_run import BrowserAgentRun
from src.db.models.user import User
from src.db.session import get_session_factory
from src.jobs.job_lock_service import acquire_named_job_lock, release_named_job_lock
from src.shared.config.settings import Settings, get_settings
from src.shared.schemas.browser_agent import (
	BrowserAgentCancelResponse,
	BrowserAgentRunCreateRequest,
	BrowserAgentRunListResponse,
	BrowserAgentRunResponse,
)

if TYPE_CHECKING:
	pass


BROWSER_AGENT_WORKER_LOCK_NAME = 'utw:browser_agent_worker'
logger = logging.getLogger(__name__)


class BrowserAgentRunNotFoundError(ValueError):
	"""Raised when the requested browser-agent run does not exist."""


class BrowserAgentAdmissionError(ValueError):
	"""Raised when a user cannot queue another browser-agent run."""


class BrowserAgentRunAlreadyFinishedError(ValueError):
	"""Raised when a run cannot be cancelled because it already finished."""


@dataclass(frozen=True)
class BrowserAgentClaimResult:
	"""Claimed queued run ready for worker execution."""

	run_id: UUID


def queue_browser_agent_run(
	session: Session,
	*,
	user: User,
	request: BrowserAgentRunCreateRequest,
	settings: Settings | None = None,
) -> BrowserAgentRunResponse:
	"""Queue a new browser-agent run for an authenticated user."""
	cfg = settings or get_settings()
	_validate_browser_agent_enabled(cfg)
	_assert_user_queue_capacity(session, user_id=user.id, settings=cfg)

	now = datetime.now(UTC)
	run = BrowserAgentRun(
		user_id=user.id,
		status='queued',
		task_prompt=request.task_prompt,
		start_url=request.start_url,
		allowed_domains=request.allowed_domains,
		max_steps=request.max_steps or cfg.browser_agent_default_max_steps,
		step_timeout_seconds=cfg.browser_agent_step_timeout_seconds,
		llm_timeout_seconds=cfg.browser_agent_llm_timeout_seconds,
		queued_at=now,
		llm_provider=cfg.ai_provider,
		llm_model=cfg.ai_model,
	)
	session.add(run)
	session.flush()
	return serialize_browser_agent_run(run)


def list_browser_agent_runs_for_user(
	session: Session,
	*,
	user_id: UUID,
	settings: Settings | None = None,
	limit: int = 10,
) -> BrowserAgentRunListResponse:
	"""Return recent browser-agent runs plus effective current-user limits."""
	cfg = settings or get_settings()
	items = (
		session.execute(
			select(BrowserAgentRun)
			.where(BrowserAgentRun.user_id == user_id)
			.order_by(BrowserAgentRun.created_at.desc())
			.limit(limit)
		)
		.scalars()
		.all()
	)
	return BrowserAgentRunListResponse(
		items=[serialize_browser_agent_run(item) for item in items],
		max_concurrent_runs_per_user=cfg.browser_agent_max_concurrent_runs_per_user,
		max_queued_runs_per_user=cfg.browser_agent_max_queued_runs_per_user,
		max_global_running_runs=cfg.browser_agent_max_global_running_runs,
		current_user_running_count=_count_runs(session, user_id=user_id, statuses=('running', 'cancelling')),
		current_user_queued_count=_count_runs(session, user_id=user_id, statuses=('queued',)),
		global_running_count=_count_runs(session, statuses=('running', 'cancelling')),
	)


def request_browser_agent_run_cancellation(
	session: Session,
	*,
	user_id: UUID,
	run_id: UUID,
) -> BrowserAgentCancelResponse:
	"""Cancel a queued or running browser-agent run owned by the current user."""
	run = session.execute(
		select(BrowserAgentRun).where(
			BrowserAgentRun.id == run_id,
			BrowserAgentRun.user_id == user_id,
		)
	).scalar_one_or_none()
	if run is None:
		raise BrowserAgentRunNotFoundError(f"browser agent run '{run_id}' was not found")

	now = datetime.now(UTC)
	if run.status == 'queued':
		run.status = 'cancelled'
		run.cancel_requested_at = now
		run.finished_at = now
		session.flush()
		return BrowserAgentCancelResponse(
			run=serialize_browser_agent_run(run),
			cancelled_immediately=True,
		)

	if run.status in {'running', 'cancelling'}:
		run.status = 'cancelling'
		run.cancel_requested_at = now
		session.flush()
		return BrowserAgentCancelResponse(
			run=serialize_browser_agent_run(run),
			cancelled_immediately=False,
		)

	raise BrowserAgentRunAlreadyFinishedError(f"browser agent run '{run_id}' is already in terminal status '{run.status}'")


def claim_next_browser_agent_run(
	session: Session,
	*,
	settings: Settings | None = None,
) -> BrowserAgentClaimResult | None:
	"""Claim the next admissible queued browser-agent run for worker execution."""
	cfg = settings or get_settings()
	_validate_browser_agent_enabled(cfg)
	if _count_runs(session, statuses=('running', 'cancelling')) >= cfg.browser_agent_max_global_running_runs:
		return None

	candidate_ids = (
		session.execute(
			select(BrowserAgentRun.id)
			.where(BrowserAgentRun.status == 'queued')
			.order_by(BrowserAgentRun.queued_at.asc())
			.limit(25)
			.with_for_update(skip_locked=True)
		)
		.scalars()
		.all()
	)

	now = datetime.now(UTC)
	for candidate_id in candidate_ids:
		run = session.get(BrowserAgentRun, candidate_id)
		if run is None or run.status != 'queued':
			continue
		user_running_count = _count_runs(
			session,
			user_id=run.user_id,
			statuses=('running', 'cancelling'),
		)
		if user_running_count >= cfg.browser_agent_max_concurrent_runs_per_user:
			continue

		run.status = 'running'
		run.started_at = now
		run.last_heartbeat_at = now
		run.error_message = None
		session.flush()
		return BrowserAgentClaimResult(run_id=run.id)

	return None


def run_browser_agent_worker_once(
	*,
	settings: Settings | None = None,
) -> BrowserAgentRunResponse | None:
	"""Claim and execute exactly one queued browser-agent run."""
	cfg = settings or get_settings()
	session_factory = get_session_factory()
	with session_factory() as session:
		claim = _claim_next_browser_agent_run_with_lock(session, settings=cfg)
		if claim is None:
			session.commit()
			return None
		session.commit()

	asyncio.run(_execute_browser_agent_run(claim.run_id, settings=cfg))

	with session_factory() as session:
		run = session.get(BrowserAgentRun, claim.run_id)
		if run is None:
			raise BrowserAgentRunNotFoundError(f"browser agent run '{claim.run_id}' was not found after execution")
		return serialize_browser_agent_run(run)


def fail_stale_browser_agent_runs(
	session: Session,
	*,
	settings: Settings | None = None,
	now: datetime | None = None,
) -> int:
	"""Fail browser-agent runs whose worker heartbeat has gone stale."""
	cfg = settings or get_settings()
	current_time = now or datetime.now(UTC)
	cutoff = current_time - timedelta(seconds=cfg.browser_agent_worker_stale_heartbeat_seconds)

	stale_runs = (
		session.execute(
			select(BrowserAgentRun).where(
				BrowserAgentRun.status.in_(('running', 'cancelling')),
				or_(
					BrowserAgentRun.last_heartbeat_at <= cutoff,
					BrowserAgentRun.last_heartbeat_at.is_(None),
					BrowserAgentRun.started_at <= cutoff,
				),
			)
		)
		.scalars()
		.all()
	)

	if not stale_runs:
		return 0

	for run in stale_runs:
		if run.status == 'cancelling' or run.cancel_requested_at is not None:
			run.status = 'cancelled'
			run.error_message = 'browser agent worker exited before acknowledging cancellation'
		else:
			run.status = 'failed'
			run.error_message = 'browser agent worker heartbeat expired'
		run.finished_at = current_time
		run.last_heartbeat_at = current_time

	session.flush()
	logger.warning('browser_agent_stale_runs_failed count=%s cutoff=%s', len(stale_runs), cutoff.isoformat())
	return len(stale_runs)


async def _execute_browser_agent_run(run_id: UUID, *, settings: Settings) -> None:
	session_factory = get_session_factory()
	with session_factory() as session:
		run = session.get(BrowserAgentRun, run_id)
		if run is None:
			raise BrowserAgentRunNotFoundError(f"browser agent run '{run_id}' was not found")

		if run.status not in {'running', 'cancelling'}:
			return

		ai_runtime = build_ai_runtime(settings)
		if ai_runtime.llm is None:
			run.status = 'failed'
			run.error_message = 'browser agent execution requires an enabled AI runtime'
			run.finished_at = datetime.now(UTC)
			session.commit()
			return

		agent_class, browser_session_class = _get_browser_use_runtime_classes()
		browser_session = browser_session_class(
			headless=True,
			allowed_domains=run.allowed_domains,
			captcha_solver=True,
		)
		task = run.task_prompt
		if run.start_url:
			task = f'{task}\n\nStart at: {run.start_url}'

		async def should_stop() -> bool:
			with session_factory() as callback_session:
				latest = callback_session.get(BrowserAgentRun, run_id)
				if latest is None:
					return True
				latest.last_heartbeat_at = datetime.now(UTC)
				callback_session.commit()
				return latest.status == 'cancelling' or latest.cancel_requested_at is not None

		agent = agent_class(
			task=task,
			llm=ai_runtime.llm,
			fallback_llm=ai_runtime.fallback_llm,
			browser_session=browser_session,
			register_should_stop_callback=should_stop,
			step_timeout=run.step_timeout_seconds,
			llm_timeout=run.llm_timeout_seconds,
		)

		try:
			history = await agent.run(max_steps=run.max_steps)
			await browser_session.stop()
			session.refresh(run)
			now = datetime.now(UTC)
			if run.status == 'cancelling' or run.cancel_requested_at is not None:
				run.status = 'cancelled'
			else:
				run.status = 'completed'
			run.final_result_text = history.final_result()
			run.finished_at = now
			run.last_heartbeat_at = now
			session.commit()
		except Exception as exc:
			try:
				await browser_session.stop()
			except Exception:
				pass
			session.refresh(run)
			now = datetime.now(UTC)
			if run.status == 'cancelling' or run.cancel_requested_at is not None:
				run.status = 'cancelled'
			else:
				run.status = 'failed'
				run.error_message = str(exc)
			run.finished_at = now
			run.last_heartbeat_at = now
			session.commit()


def serialize_browser_agent_run(run: BrowserAgentRun) -> BrowserAgentRunResponse:
	"""Convert a browser-agent run model into an API response payload."""
	return BrowserAgentRunResponse(
		id=run.id,
		user_id=run.user_id,
		status=run.status,
		task_prompt=run.task_prompt,
		start_url=run.start_url,
		allowed_domains=run.allowed_domains,
		max_steps=run.max_steps,
		step_timeout_seconds=run.step_timeout_seconds,
		llm_timeout_seconds=run.llm_timeout_seconds,
		queued_at=run.queued_at,
		started_at=run.started_at,
		finished_at=run.finished_at,
		cancel_requested_at=run.cancel_requested_at,
		last_heartbeat_at=run.last_heartbeat_at,
		error_message=run.error_message,
		final_result_text=run.final_result_text,
		llm_provider=run.llm_provider,
		llm_model=run.llm_model,
		created_at=run.created_at,
		updated_at=run.updated_at,
	)


def _count_runs(
	session: Session,
	*,
	statuses: tuple[str, ...],
	user_id: UUID | None = None,
) -> int:
	query: Select[tuple[int]] = select(func.count()).select_from(BrowserAgentRun).where(BrowserAgentRun.status.in_(statuses))
	if user_id is not None:
		query = query.where(BrowserAgentRun.user_id == user_id)
	return int(session.execute(query).scalar_one())


def _assert_user_queue_capacity(
	session: Session,
	*,
	user_id: UUID,
	settings: Settings,
) -> None:
	current_user_queued_count = _count_runs(session, user_id=user_id, statuses=('queued',))
	if current_user_queued_count >= settings.browser_agent_max_queued_runs_per_user:
		raise BrowserAgentAdmissionError('browser_agent_queue_limit_reached')


def _validate_browser_agent_enabled(settings: Settings) -> None:
	if not settings.browser_agent_enabled:
		raise BrowserAgentAdmissionError('browser_agent_disabled')
	if settings.ai_provider == 'disabled':
		raise BrowserAgentAdmissionError('browser_agent_requires_enabled_ai_provider')


def _claim_next_browser_agent_run_with_lock(
	session: Session,
	*,
	settings: Settings,
) -> BrowserAgentClaimResult | None:
	"""Serialize claim admission so concurrent workers cannot over-claim capacity."""
	if not _should_use_worker_claim_lock(session):
		return claim_next_browser_agent_run(session, settings=settings)

	lock_acquired = False
	try:
		lock_acquired = acquire_named_job_lock(
			session,
			job_name=BROWSER_AGENT_WORKER_LOCK_NAME,
		)
		if not lock_acquired:
			return None
		return claim_next_browser_agent_run(session, settings=settings)
	finally:
		if lock_acquired:
			released = release_named_job_lock(
				session,
				job_name=BROWSER_AGENT_WORKER_LOCK_NAME,
			)
			if not released:
				raise RuntimeError('expected browser-agent worker claim lock release to succeed')


def _should_use_worker_claim_lock(session: Session) -> bool:
	"""Enable advisory claim locking only on PostgreSQL-backed sessions."""
	bind = session.get_bind()
	return bind is not None and bind.dialect.name == 'postgresql'


def _get_browser_use_runtime_classes() -> tuple[type[Any], type[Any]]:
	from browser_use import Agent, BrowserSession

	return Agent, BrowserSession
