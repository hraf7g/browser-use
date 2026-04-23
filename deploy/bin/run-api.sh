#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"

cd "${APP_DIR}"
exec python -m uvicorn src.api.app:app --host 0.0.0.0 --port "${UTW_PORT:-8000}"
