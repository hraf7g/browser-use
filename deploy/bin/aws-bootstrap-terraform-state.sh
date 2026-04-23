#!/usr/bin/env bash

set -euo pipefail

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing required command: $1" >&2
    exit 1
  }
}

require_command aws

STATE_BUCKET="${1:-}"
AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-}}"

if [[ -z "${STATE_BUCKET}" ]]; then
  echo "usage: aws-bootstrap-terraform-state.sh <state-bucket-name>" >&2
  exit 1
fi

if [[ -z "${AWS_REGION}" ]]; then
  AWS_REGION=$(aws configure get region 2>/dev/null || true)
fi

if [[ -z "${AWS_REGION}" ]]; then
  echo "AWS_REGION or AWS_DEFAULT_REGION must be set" >&2
  exit 1
fi

if aws s3api head-bucket --bucket "${STATE_BUCKET}" >/dev/null 2>&1; then
  echo "terraform state bucket already exists: ${STATE_BUCKET}"
else
  if [[ "${AWS_REGION}" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "${STATE_BUCKET}" >/dev/null
  else
    aws s3api create-bucket \
      --bucket "${STATE_BUCKET}" \
      --create-bucket-configuration "LocationConstraint=${AWS_REGION}" >/dev/null
  fi
fi

aws s3api put-bucket-versioning \
  --bucket "${STATE_BUCKET}" \
  --versioning-configuration Status=Enabled >/dev/null

aws s3api put-bucket-encryption \
  --bucket "${STATE_BUCKET}" \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' >/dev/null

aws s3api put-public-access-block \
  --bucket "${STATE_BUCKET}" \
  --public-access-block-configuration 'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true' >/dev/null

printf 'terraform_state_bucket=%s\n' "${STATE_BUCKET}"
printf 'terraform_state_region=%s\n' "${AWS_REGION}"
