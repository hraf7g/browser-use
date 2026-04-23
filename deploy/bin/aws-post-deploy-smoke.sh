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
require_command curl
require_command terraform

cluster_name=$(terraform -chdir="${TERRAFORM_DIR}" output -raw ecs_cluster_name)
api_service=$(terraform -chdir="${TERRAFORM_DIR}" output -raw api_service_name)
frontend_service=$(terraform -chdir="${TERRAFORM_DIR}" output -raw frontend_service_name)
browser_worker_service=$(terraform -chdir="${TERRAFORM_DIR}" output -raw browser_worker_service_name)
app_url=$(terraform -chdir="${TERRAFORM_DIR}" output -raw app_url)
scheduler_dlq_url=$(terraform -chdir="${TERRAFORM_DIR}" output -raw scheduler_dlq_url)

aws ecs wait services-stable \
  --cluster "${cluster_name}" \
  --services "${api_service}" "${frontend_service}" "${browser_worker_service}"

curl -fsS "${app_url}/" >/dev/null
curl -fsS "${app_url}/health" >/dev/null
curl -fsS "${app_url}/health/ready" >/dev/null

dlq_visible=$(aws sqs get-queue-attributes \
  --queue-url "${scheduler_dlq_url}" \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' \
  --output text)

printf 'smoke_app_url=%s\n' "${app_url}"
printf 'smoke_cluster=%s\n' "${cluster_name}"
printf 'smoke_services=%s,%s,%s\n' "${api_service}" "${frontend_service}" "${browser_worker_service}"
printf 'smoke_scheduler_dlq_visible_messages=%s\n' "${dlq_visible}"

if [[ "${dlq_visible}" != "0" ]]; then
  echo "scheduler DLQ is not empty; inspect failed scheduled invocations before go-live" >&2
  exit 1
fi
