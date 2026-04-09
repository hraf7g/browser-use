from __future__ import annotations

import os
from datetime import datetime

from src.jobs.match_recent_tenders_job_service import run_match_recent_tenders_job


def run() -> int:
    """
    Execute the recent-tender matching job once from environment input.

    Required env:
        - UTW_MATCH_SINCE_ISO: ISO-8601 timestamp with timezone
    """
    since_raw = os.environ.get("UTW_MATCH_SINCE_ISO", "").strip()
    if not since_raw:
        raise ValueError("UTW_MATCH_SINCE_ISO must be set")

    since = datetime.fromisoformat(since_raw)
    matches_created = run_match_recent_tenders_job(since=since)

    print(f"run_match_recent_tenders_once_since={since.isoformat()}")
    print(f"run_match_recent_tenders_once_matches_created={matches_created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
