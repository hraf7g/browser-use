from __future__ import annotations

from src.jobs.send_pending_daily_briefs_job_service import (
    SendPendingDailyBriefsJobResult,
    run_send_pending_daily_briefs_job,
)


def run() -> int:
    """
    Execute the pending daily-brief dispatch job once.

    Exit codes:
        - 0 when the job succeeds
        - 1 when the job fails
    """
    try:
        result = run_send_pending_daily_briefs_job()
    except Exception:
        result = SendPendingDailyBriefsJobResult(
            processed_user_count=0,
            sent_delivery_count=0,
            skipped_user_count=0,
            overall_status="failed",
        )
        print(f"run_send_pending_daily_briefs_once_overall_status={result.overall_status}")
        print(
            "run_send_pending_daily_briefs_once_processed_user_count="
            f"{result.processed_user_count}"
        )
        print(
            "run_send_pending_daily_briefs_once_sent_delivery_count="
            f"{result.sent_delivery_count}"
        )
        print(
            "run_send_pending_daily_briefs_once_skipped_user_count="
            f"{result.skipped_user_count}"
        )
        return 1

    print(f"run_send_pending_daily_briefs_once_overall_status={result.overall_status}")
    print(
        "run_send_pending_daily_briefs_once_processed_user_count="
        f"{result.processed_user_count}"
    )
    print(
        "run_send_pending_daily_briefs_once_sent_delivery_count="
        f"{result.sent_delivery_count}"
    )
    print(
        "run_send_pending_daily_briefs_once_skipped_user_count="
        f"{result.skipped_user_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
