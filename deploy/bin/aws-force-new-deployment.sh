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

require_command aws
require_command terraform

cluster_name=$(terraform -chdir="${TERRAFORM_DIR}" output -raw ecs_cluster_name)
api_service=$(terraform -chdir="${TERRAFORM_DIR}" output -raw api_service_name)
frontend_service=$(terraform -chdir="${TERRAFORM_DIR}" output -raw frontend_service_name)
browser_worker_service=$(terraform -chdir="${TERRAFORM_DIR}" output -raw browser_worker_service_name)

aws ecs update-service \
  --cluster "${cluster_name}" \
  --service "${api_service}" \
  --force-new-deployment >/dev/null

aws ecs update-service \
  --cluster "${cluster_name}" \
  --service "${frontend_service}" \
  --force-new-deployment >/dev/null

aws ecs update-service \
  --cluster "${cluster_name}" \
  --service "${browser_worker_service}" \
  --force-new-deployment >/dev/null

aws ecs wait services-stable \
  --cluster "${cluster_name}" \
  --services "${api_service}" "${frontend_service}" "${browser_worker_service}"

printf 'services_stable_cluster=%s\n' "${cluster_name}"
