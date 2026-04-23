# AWS Secret Matrix

This document defines where each production configuration value should live for AWS deployment.

## Rules

- Do not store production secrets in the repo.
- Do not store secrets in `.venv`.
- Prefer EC2 instance profile or ECS task role access for Bedrock and SES.
- Use `Secrets Manager` for true secrets.
- Use `SSM Parameter Store` for non-secret runtime config.

## Backend

| Variable | Required | Sensitive | Store | Notes |
| --- | --- | --- | --- | --- |
| `UTW_ENVIRONMENT` | yes | no | SSM | Set to `production`. |
| `UTW_DEBUG` | yes | no | SSM | Must be `false` in production. |
| `UTW_HOST` | yes | no | SSM | `127.0.0.1` behind Nginx or ALB target proxy. |
| `UTW_PORT` | yes | no | SSM | Backend listener port. |
| `UTW_DATABASE_URL` | yes | yes | Secrets Manager | Full RDS connection string. |
| `UTW_AUTH_SECRET_KEY` | yes | yes | Secrets Manager | Long random signing secret. |
| `UTW_AUTH_ISSUER` | yes | no | SSM | Keep stable after go-live. |
| `UTW_AUTH_AUDIENCE` | yes | no | SSM | Keep stable after go-live. |
| `UTW_AUTH_ACCESS_TOKEN_TTL_MINUTES` | yes | no | SSM | `60` is a reasonable default. |
| `UTW_AUTH_COOKIE_NAME` | yes | no | SSM | Must match frontend build value. |
| `UTW_AUTH_COOKIE_PATH` | yes | no | SSM | Usually `/`. |
| `UTW_AUTH_COOKIE_DOMAIN` | no | no | SSM | Optional shared parent domain. |
| `UTW_AUTH_COOKIE_SAME_SITE` | yes | no | SSM | Usually `lax`. |
| `UTW_AUTH_COOKIE_SECURE` | yes | no | SSM | Must be `true` in production. |
| `UTW_PASSWORD_RESET_TOKEN_TTL_MINUTES` | yes | no | SSM | Default `60`. |
| `UTW_FRONTEND_BASE_URL` | yes | no | SSM | Public frontend URL, `https://...`. |
| `UTW_CORS_ALLOW_ORIGINS` | yes | no | SSM | Comma-separated frontend origins only. |
| `UTW_OPERATOR_API_KEY` | if operator routes enabled | yes | Secrets Manager | Rotate separately from auth secret. |
| `UTW_EMAIL_DELIVERY_BACKEND` | yes | no | SSM | Set to `ses`. |
| `UTW_EMAIL_SENDER` | yes | no | SSM | Verified SES sender identity. |
| `UTW_EMAIL_REPLY_TO` | no | no | SSM | Optional reply-to address. |
| `UTW_EMAIL_SES_CONFIGURATION_SET` | no | no | SSM | Optional SES configuration set. |
| `UTW_EMAIL_SES_FROM_ARN` | no | no | SSM | Optional delegated SES identity ARN. |
| `UTW_AWS_REGION` | yes | no | SSM | Must match SES/Bedrock region strategy. |
| `UTW_AI_PROVIDER` | yes if AI enabled | no | SSM | Use `bedrock_anthropic`. |
| `UTW_AI_MODEL` | yes if AI enabled | no | SSM | Recommended `anthropic.claude-sonnet-4-6`. |
| `UTW_AI_FALLBACK_MODEL` | no | no | SSM | Optional `anthropic.claude-haiku-4-5`. |
| `UTW_AI_BEDROCK_USE_AMBIENT_CREDENTIALS` | yes if AI enabled | no | SSM | Keep `true` on AWS. |
| `UTW_AI_MAX_TOKENS` | yes if AI enabled | no | SSM | Bound this intentionally. |
| `UTW_AI_TEMPERATURE` | yes if AI enabled | no | SSM | Keep `0.0` for deterministic summaries. |
| `UTW_AI_SUMMARY_BATCH_SIZE` | yes if AI enabled | no | SSM | Tune based on Bedrock cost/runtime. |
| `UTW_AI_SUMMARY_MAX_ATTEMPTS` | yes if AI enabled | no | SSM | Keep bounded, e.g. `3`. |
| `UTW_AI_DAILY_REQUEST_BUDGET` | yes if AI enabled | no | SSM | Hard daily request ceiling enforced in-app before invoking Bedrock. |
| `UTW_AI_DAILY_RESERVED_TOKEN_BUDGET` | yes if AI enabled | no | SSM | Hard daily token ceiling enforced using Bedrock `CountTokens` + `UTW_AI_MAX_TOKENS`. |
| `UTW_BROWSER_AGENT_ENABLED` | yes if browser runs enabled | no | SSM | Enables authenticated user browser-agent queueing. |
| `UTW_BROWSER_AGENT_DEFAULT_MAX_STEPS` | yes if browser runs enabled | no | SSM | Default live browser-run step ceiling. |
| `UTW_BROWSER_AGENT_STEP_TIMEOUT_SECONDS` | yes if browser runs enabled | no | SSM | Per-step timeout for live browser runs. |
| `UTW_BROWSER_AGENT_LLM_TIMEOUT_SECONDS` | yes if browser runs enabled | no | SSM | Per-model-call timeout for live browser runs. |
| `UTW_BROWSER_AGENT_MAX_CONCURRENT_RUNS_PER_USER` | yes if browser runs enabled | no | SSM | Per-user running browser-run cap. |
| `UTW_BROWSER_AGENT_MAX_QUEUED_RUNS_PER_USER` | yes if browser runs enabled | no | SSM | Per-user queued run admission limit. |
| `UTW_BROWSER_AGENT_MAX_GLOBAL_RUNNING_RUNS` | yes if browser runs enabled | no | SSM | Global running browser-run cap across the app. |
| `UTW_BROWSER_AGENT_WORKER_POLL_SECONDS` | yes if browser runs enabled | no | SSM | Idle poll interval for the dedicated browser worker service. |
| `UTW_BROWSER_AGENT_WORKER_STALE_HEARTBEAT_SECONDS` | yes if browser runs enabled | no | SSM | Marks stuck running browser-agent runs stale after this heartbeat age. |
| `BROWSER_USE_REQUIRE_EXPLICIT_LLM` | yes if any agent runtime enabled | no | SSM | Must stay `true`. |
| `DEFAULT_LLM` | yes if any agent runtime enabled | no | SSM | Explicit Bedrock model id. |
| `BROWSER_USE_AWS_REGION` | yes if any agent runtime enabled | no | SSM | Can match `UTW_AWS_REGION`. |

## Frontend

| Variable | Required | Sensitive | Store | Notes |
| --- | --- | --- | --- | --- |
| `NODE_ENV` | yes | no | SSM | Set to `production`. |
| `PORT` | yes | no | SSM | Frontend listener port. |
| `HOSTNAME` | yes | no | SSM | Usually `127.0.0.1` behind reverse proxy. |
| `NEXT_PUBLIC_API_URL` | yes | no | SSM | Public API base URL, compiled into build. |
| `NEXT_PUBLIC_AUTH_COOKIE_NAME` | yes | no | SSM | Must match backend cookie name. |
| `UTW_OPERATOR_API_KEY` | if operator UI proxy enabled | yes | Secrets Manager | Server-only env for the Next.js operator proxy. Never expose as `NEXT_PUBLIC_*`. |

## AWS-Native Credentials

These should not be put into `.env` in production if the app runs on AWS with IAM roles:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`

Use:

- EC2 instance profile for EC2 deployments
- ECS task role for ECS deployments

For AI budget enforcement, the runtime also needs Bedrock permission to call `CountTokens`, not only invoke permissions.

## Bedrock Recommendation

Use:

- primary model: `anthropic.claude-sonnet-4-6`
- optional fallback: `anthropic.claude-haiku-4-5`

This app does not require `BROWSER_USE_API_KEY` when the runtime stays on explicit Bedrock configuration.
