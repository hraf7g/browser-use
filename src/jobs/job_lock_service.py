from __future__ import annotations

import hashlib
import logging
from typing import Final

from sqlalchemy import select
from sqlalchemy.orm import Session

MAX_POSTGRES_BIGINT: Final[int] = (1 << 63) - 1


def acquire_named_job_lock(
    session: Session,
    *,
    job_name: str,
) -> bool:
    """
    Try to acquire a session-scoped PostgreSQL advisory lock for a job name.

    Notes:
        - lock ownership is bound to the current database connection
        - callers should release the lock before returning pooled connections
        - returns False when another session already holds the same lock
    """
    lock_key = _build_job_lock_key(job_name)
    return bool(
        session.execute(select(_pg_try_advisory_lock(lock_key))).scalar_one()
    )


def release_named_job_lock(
    session: Session,
    *,
    job_name: str,
) -> bool:
    """
    Release a session-scoped PostgreSQL advisory lock for a job name.

    Returns:
        bool:
            - True when the current connection held and released the lock
            - False when the current connection did not hold the lock
    """
    lock_key = _build_job_lock_key(job_name)
    return bool(session.execute(select(_pg_advisory_unlock(lock_key))).scalar_one())


def finalize_named_job_lock(
    session: Session,
    *,
    job_name: str,
    logger: logging.Logger,
    active_error: Exception | None = None,
) -> None:
    """
    Best-effort finalize a named advisory lock without changing the primary job outcome.

    Notes:
        - lock release failures are logged but do not override a successful job result
        - when a job already failed, release anomalies are also logged and suppressed so the
          original error remains the surfaced failure
    """
    try:
        released = release_named_job_lock(
            session,
            job_name=job_name,
        )
    except Exception:
        logger.exception(
            'job_lock_release_failed',
            extra={
                'job_name': job_name,
                'active_error_present': active_error is not None,
            },
        )
        return

    if not released:
        logger.warning(
            'job_lock_release_failed',
            extra={
                'job_name': job_name,
                'active_error_present': active_error is not None,
                'reason': 'lock_not_held',
            },
        )


def _build_job_lock_key(job_name: str) -> int:
    """Build a deterministic positive bigint advisory-lock key from a job name."""
    cleaned = job_name.strip()
    if not cleaned:
        raise ValueError("job_name must not be empty")

    digest = hashlib.sha256(cleaned.encode("utf-8")).digest()
    raw_value = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return raw_value & MAX_POSTGRES_BIGINT


def _pg_try_advisory_lock(lock_key: int):
    """Return the SQLAlchemy function object for pg_try_advisory_lock."""
    from sqlalchemy import func

    return func.pg_try_advisory_lock(lock_key)


def _pg_advisory_unlock(lock_key: int):
    """Return the SQLAlchemy function object for pg_advisory_unlock."""
    from sqlalchemy import func

    return func.pg_advisory_unlock(lock_key)
