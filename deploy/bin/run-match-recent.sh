#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/utw/current"
SINCE_MINUTES="${UTW_MATCH_LOOKBACK_MINUTES:-120}"

export UTW_MATCH_SINCE_ISO="$(python3 - <<'PY'
from datetime import datetime, timedelta, timezone
import os

minutes = int(os.environ.get("UTW_MATCH_LOOKBACK_MINUTES", "120"))
since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
print(since.isoformat())
PY
)"

cd "${APP_DIR}"
exec "${APP_DIR}/.venv/bin/python" -m src.jobs.run_match_recent_tenders_once
