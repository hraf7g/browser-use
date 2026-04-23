#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
SINCE_MINUTES="${UTW_ENRICH_LOOKBACK_MINUTES:-180}"

export UTW_ENRICH_SINCE_ISO="$(python - <<'PY'
from datetime import datetime, timedelta, timezone
import os

minutes = int(os.environ.get("UTW_ENRICH_LOOKBACK_MINUTES", "180"))
since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
print(since.isoformat())
PY
)"

cd "${APP_DIR}"
exec python -m src.jobs.run_enrich_recent_tenders_once
