#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"

cd "${APP_DIR}"
exec python -m alembic upgrade head
