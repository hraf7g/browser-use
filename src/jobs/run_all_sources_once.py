from __future__ import annotations

import sys

from src.jobs.run_all_sources_job_service import run_all_sources_job


def run() -> int:
    """
    Execute the all-sources job once and print a compact summary.

    Exit codes:
        - 0 when all sources succeed
        - 1 when any source fails
    """
    result = run_all_sources_job()

    print(f"run_all_sources_once_overall_status={result.overall_status}")
    print(f"run_all_sources_once_total_sources={result.total_sources}")
    print(f"run_all_sources_once_success_count={result.success_count}")
    print(f"run_all_sources_once_failed_count={result.failed_count}")

    for item in result.results:
        print(
            "run_all_sources_once_result="
            f"{item.source_name}|{item.status}|{item.created_tender_count}|"
            f"{item.updated_tender_count}"
        )

    if result.overall_status == "success":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(run())
