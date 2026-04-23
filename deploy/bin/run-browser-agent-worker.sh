#!/usr/bin/env bash

set -euo pipefail

exec python -m src.jobs.run_browser_agent_worker_service
