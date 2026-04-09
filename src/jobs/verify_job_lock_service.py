from __future__ import annotations

from src.db.session import get_session_factory
from src.jobs.job_lock_service import acquire_named_job_lock, release_named_job_lock

JOB_LOCK_NAME = "utw:verify_job_lock_service"


def run() -> None:
    """
    Perform a persisted verification of the PostgreSQL job advisory lock helper.

    This script verifies:
        - session A can acquire the named lock
        - session B cannot acquire it while A holds it
        - after A releases it, session B can acquire it
    """
    session_factory = get_session_factory()

    with session_factory() as session_a, session_factory() as session_b:
        acquired_by_a = acquire_named_job_lock(session_a, job_name=JOB_LOCK_NAME)
        if not acquired_by_a:
            raise ValueError("expected session A to acquire the job lock")

        acquired_by_b_while_a_holds = acquire_named_job_lock(
            session_b,
            job_name=JOB_LOCK_NAME,
        )
        if acquired_by_b_while_a_holds:
            raise ValueError(
                "expected session B to be blocked while session A holds the job lock"
            )

        released_by_a = release_named_job_lock(session_a, job_name=JOB_LOCK_NAME)
        if not released_by_a:
            raise ValueError("expected session A to release the job lock")

        acquired_by_b_after_release = acquire_named_job_lock(
            session_b,
            job_name=JOB_LOCK_NAME,
        )
        if not acquired_by_b_after_release:
            raise ValueError(
                "expected session B to acquire the job lock after session A released it"
            )

        released_by_b = release_named_job_lock(session_b, job_name=JOB_LOCK_NAME)
        if not released_by_b:
            raise ValueError("expected session B to release the job lock")

        print(f"verify_job_lock_name={JOB_LOCK_NAME}")
        print(f"verify_job_lock_acquired_by_a={acquired_by_a}")
        print(
            "verify_job_lock_acquired_by_b_while_a_holds="
            f"{acquired_by_b_while_a_holds}"
        )
        print(f"verify_job_lock_released_by_a={released_by_a}")
        print(
            "verify_job_lock_acquired_by_b_after_release="
            f"{acquired_by_b_after_release}"
        )
        print(f"verify_job_lock_released_by_b={released_by_b}")


if __name__ == "__main__":
    run()
