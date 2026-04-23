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
require_command docker
require_command terraform
require_command git

TAG="${1:-$(git -C "${REPO_ROOT}" rev-parse --short=12 HEAD)}"
AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"
if [[ -z "${AWS_REGION}" ]]; then
  AWS_REGION=$(aws configure get region 2>/dev/null || true)
fi
if [[ -z "${AWS_REGION}" ]]; then
  echo "AWS_REGION or AWS_DEFAULT_REGION must be set" >&2
  exit 1
fi

backend_repo=$(terraform -chdir="${TERRAFORM_DIR}" output -raw backend_ecr_repository_url)
frontend_repo=$(terraform -chdir="${TERRAFORM_DIR}" output -raw frontend_ecr_repository_url)
app_url="${APP_URL:-}"
if [[ -z "${app_url}" ]]; then
  app_url=$(terraform -chdir="${TERRAFORM_DIR}" output -raw app_url)
fi
cookie_name="utw_access_token"

account_registry=$(printf '%s\n' "${backend_repo}" | cut -d/ -f1)

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${account_registry}"

docker build \
  -f "${REPO_ROOT}/deploy/docker/backend.Dockerfile" \
  -t "${backend_repo}:${TAG}" \
  "${REPO_ROOT}"
docker push "${backend_repo}:${TAG}"

docker build \
  -f "${REPO_ROOT}/deploy/docker/frontend.Dockerfile" \
  --build-arg "NEXT_PUBLIC_API_URL=${app_url}" \
  --build-arg "NEXT_PUBLIC_AUTH_COOKIE_NAME=${cookie_name}" \
  -t "${frontend_repo}:${TAG}" \
  "${REPO_ROOT}"
docker push "${frontend_repo}:${TAG}"

printf 'backend_image=%s:%s\n' "${backend_repo}" "${TAG}"
printf 'frontend_image=%s:%s\n' "${frontend_repo}" "${TAG}"
