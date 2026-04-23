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

require_command python3

TAG="${1:-}"
if [[ -z "${TAG}" ]]; then
  echo "usage: aws-write-terraform-vars.sh <image-tag>" >&2
  exit 1
fi

required_envs=(
  AWS_REGION
  DOMAIN_NAME
  HOSTED_ZONE_NAME
  SES_SENDER_EMAIL
  OPERATOR_EMAIL
)

for env_name in "${required_envs[@]}"; do
  if [[ -z "${!env_name:-}" ]]; then
    echo "${env_name} must be set" >&2
    exit 1
  fi
done

TFVARS_PATH="${TERRAFORM_DIR}/deploy.auto.tfvars.json"

TFVARS_PATH="${TFVARS_PATH}" IMAGE_TAG="${TAG}" python3 - <<'PY'
import json
import os
from pathlib import Path

required = {
    "aws_region": os.environ["AWS_REGION"],
    "backend_image_tag": os.environ["IMAGE_TAG"],
    "frontend_image_tag": os.environ["IMAGE_TAG"],
    "domain_name": os.environ["DOMAIN_NAME"],
    "hosted_zone_name": os.environ["HOSTED_ZONE_NAME"],
    "ses_sender_email": os.environ["SES_SENDER_EMAIL"],
    "operator_email": os.environ["OPERATOR_EMAIL"],
}

optional_mappings = {
    "ses_reply_to_email": "SES_REPLY_TO_EMAIL",
    "ses_configuration_set": "SES_CONFIGURATION_SET",
    "ses_from_arn": "SES_FROM_ARN",
    "alarm_email_endpoint": "ALARM_EMAIL_ENDPOINT",
    "bedrock_model_id": "BEDROCK_MODEL_ID",
    "bedrock_fallback_model_id": "BEDROCK_FALLBACK_MODEL_ID",
    "browser_worker_desired_count": "BROWSER_WORKER_DESIRED_COUNT",
    "browser_worker_min_capacity": "BROWSER_WORKER_MIN_CAPACITY",
    "browser_worker_max_capacity": "BROWSER_WORKER_MAX_CAPACITY",
}

data = dict(required)
for tf_key, env_key in optional_mappings.items():
    value = os.environ.get(env_key, "").strip()
    if value:
        data[tf_key] = value

path = Path(os.environ["TFVARS_PATH"])
path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(path)
PY
