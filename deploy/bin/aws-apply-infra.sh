#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "${SCRIPT_DIR}/../.." && pwd)
TERRAFORM_DIR="${TERRAFORM_DIR:-${REPO_ROOT}/infra/terraform}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

require_command terraform
require_command git

TAG="${1:-$(git -C "${REPO_ROOT}" rev-parse --short=12 HEAD)}"
AUTO_APPROVE="${AUTO_APPROVE:-false}"

init_args=()
if [[ -f "${TERRAFORM_DIR}/backend.hcl" ]]; then
  init_args+=("-backend-config=backend.hcl")
fi

terraform -chdir="${TERRAFORM_DIR}" init "${init_args[@]}"
terraform -chdir="${TERRAFORM_DIR}" plan

apply_args=()

if [[ "${AUTO_APPROVE}" == "true" ]]; then
  apply_args+=("-auto-approve")
fi

terraform -chdir="${TERRAFORM_DIR}" apply "${apply_args[@]}"
