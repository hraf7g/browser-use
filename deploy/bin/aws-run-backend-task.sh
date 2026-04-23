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
require_command python3

JOB_NAME="${1:-}"
if [[ -z "${JOB_NAME}" ]]; then
  echo "usage: aws-run-backend-task.sh <job-name>" >&2
  echo "supported job names: migrate seed promote-operator run-all-sources enrich-recent match-recent send-daily-briefs send-instant-alerts" >&2
  exit 1
fi

case "${JOB_NAME}" in
  migrate)
    COMMAND='["/app/deploy/bin/run-db-migrate.sh"]'
    ;;
  seed)
    COMMAND='["/app/deploy/bin/run-seed-sources.sh"]'
    ;;
  promote-operator)
    COMMAND='["/app/.venv/bin/python", "-m", "src.operator.promote_operator_user"]'
    ;;
  run-all-sources)
    COMMAND='["/app/deploy/bin/run-all-sources.sh"]'
    ;;
  enrich-recent)
    COMMAND='["/app/deploy/bin/run-enrich-recent.sh"]'
    ;;
  match-recent)
    COMMAND='["/app/deploy/bin/run-match-recent.sh"]'
    ;;
  send-daily-briefs)
    COMMAND='["/app/deploy/bin/run-send-pending-daily-briefs.sh"]'
    ;;
  send-instant-alerts)
    COMMAND='["/app/deploy/bin/run-send-pending-instant-alerts.sh"]'
    ;;
  *)
    echo "unsupported job name: ${JOB_NAME}" >&2
    exit 1
    ;;
esac

cluster_name=$(terraform -chdir="${TERRAFORM_DIR}" output -raw ecs_cluster_name)
task_definition=$(terraform -chdir="${TERRAFORM_DIR}" output -raw backend_task_definition_arn)
security_group=$(terraform -chdir="${TERRAFORM_DIR}" output -raw backend_security_group_id)
subnets_json=$(terraform -chdir="${TERRAFORM_DIR}" output -json app_private_subnet_ids)

subnet_csv=$(SUBNETS_JSON="${subnets_json}" python3 - <<'PY'
import json
import os

subnets = json.loads(os.environ["SUBNETS_JSON"])
print(",".join(subnets))
PY
)

overrides=$(COMMAND_JSON="${COMMAND}" python3 - <<'PY'
import json
import os

command = json.loads(os.environ["COMMAND_JSON"])
payload = {"containerOverrides": [{"name": "backend", "command": command}]}
print(json.dumps(payload, separators=(",", ":")))
PY
)

task_arn=$(aws ecs run-task \
  --cluster "${cluster_name}" \
  --launch-type FARGATE \
  --task-definition "${task_definition}" \
  --network-configuration "awsvpcConfiguration={subnets=[${subnet_csv}],securityGroups=[${security_group}],assignPublicIp=DISABLED}" \
  --overrides "${overrides}" \
  --query 'tasks[0].taskArn' \
  --output text)

if [[ "${task_arn}" == "None" || -z "${task_arn}" ]]; then
  echo "failed to start backend task" >&2
  exit 1
fi

aws ecs wait tasks-stopped --cluster "${cluster_name}" --tasks "${task_arn}"

task_summary=$(aws ecs describe-tasks \
  --cluster "${cluster_name}" \
  --tasks "${task_arn}" \
  --query 'tasks[0].containers[0].{exitCode:exitCode,reason:reason,lastStatus:lastStatus}' \
  --output json)

printf 'task_arn=%s\n' "${task_arn}"
printf 'task_summary=%s\n' "${task_summary}"

exit_code=$(TASK_SUMMARY="${task_summary}" python3 - <<'PY'
import json
import os

summary = json.loads(os.environ["TASK_SUMMARY"])
exit_code = summary.get("exitCode")
print("" if exit_code is None else exit_code)
PY
)

if [[ -z "${exit_code}" ]]; then
  echo "task exited without an exitCode; inspect ECS and CloudWatch logs" >&2
  exit 1
fi

exit "${exit_code}"
