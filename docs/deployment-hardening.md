# Deployment Hardening

This release state is intended for staging or production deployment after the following checks pass.

## Required Environment

Backend:

- `UTW_ENVIRONMENT=production`
- `UTW_DEBUG=false`
- `UTW_DATABASE_URL=<production postgres URL>`
- `UTW_AUTH_SECRET_KEY=<long random secret>`
- `UTW_AUTH_COOKIE_SECURE=true`
- `UTW_AUTH_COOKIE_SAME_SITE=lax` or `strict`
- `UTW_AUTH_COOKIE_PATH=/`
- `UTW_AUTH_COOKIE_DOMAIN=<optional parent domain if the frontend and API share one>`
- `UTW_CORS_ALLOW_ORIGINS=https://app.example.com,https://www.example.com`
- `UTW_OPERATOR_API_KEY=<operator key if operator routes are enabled>`
- `UTW_EMAIL_DELIVERY_BACKEND=ses`
- `UTW_EMAIL_SENDER=alerts@example.com`
- `UTW_AWS_REGION=us-east-1`
- `UTW_EMAIL_REPLY_TO=<optional reply-to address>`
- `UTW_EMAIL_SES_CONFIGURATION_SET=<optional SES configuration set>`
- `UTW_EMAIL_SES_FROM_ARN=<optional SES identity ARN>`
- `UTW_AI_PROVIDER=bedrock_anthropic` when AI is enabled
- `UTW_AI_MODEL=anthropic.claude-sonnet-4-6`
- `UTW_AI_FALLBACK_MODEL=anthropic.claude-haiku-4-5` or empty if you do not want a fallback
- `UTW_AI_BEDROCK_USE_AMBIENT_CREDENTIALS=true` for ECS task roles / EC2 instance profiles
- `UTW_AI_MAX_TOKENS=<bounded production value>`
- `UTW_AI_TEMPERATURE=0.0`
- `UTW_AI_SUMMARY_BATCH_SIZE=<bounded batch size>`
- `UTW_AI_SUMMARY_MAX_ATTEMPTS=3`
- `UTW_AI_DAILY_REQUEST_BUDGET=<hard daily request ceiling>`
- `UTW_AI_DAILY_RESERVED_TOKEN_BUDGET=<hard daily reserved-token ceiling>`
- `UTW_BROWSER_AGENT_ENABLED=true` if user-facing browser runs are enabled
- `UTW_BROWSER_AGENT_DEFAULT_MAX_STEPS=<bounded live-run step ceiling>`
- `UTW_BROWSER_AGENT_STEP_TIMEOUT_SECONDS=<bounded live-run step timeout>`
- `UTW_BROWSER_AGENT_LLM_TIMEOUT_SECONDS=<bounded live-run llm timeout>`
- `UTW_BROWSER_AGENT_MAX_CONCURRENT_RUNS_PER_USER=<per-user running cap>`
- `UTW_BROWSER_AGENT_MAX_QUEUED_RUNS_PER_USER=<per-user queue cap>`
- `UTW_BROWSER_AGENT_MAX_GLOBAL_RUNNING_RUNS=<global running cap>`
- `UTW_BROWSER_AGENT_WORKER_POLL_SECONDS=<idle worker poll interval>`
- `UTW_BROWSER_AGENT_WORKER_STALE_HEARTBEAT_SECONDS=<stale run heartbeat timeout>`
- `BROWSER_USE_REQUIRE_EXPLICIT_LLM=true` if any Browser Use agent runtime is enabled
- `DEFAULT_LLM=bedrock_anthropic:us.anthropic.claude-sonnet-4-20250514-v1:0` to force Bedrock as the runtime default
- `BROWSER_USE_AWS_REGION=us-east-1` or standard `AWS_REGION` / `AWS_DEFAULT_REGION`

Frontend:

- `NEXT_PUBLIC_API_URL=https://api.example.com`
- `NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token`
- `NEXT_PUBLIC_*` values must be set before `npm run build`; Next.js compiles them into the production bundle

## Runtime Checks

- `GET /health` for liveness
- `GET /health/ready` for database readiness
- `POST /auth/login` sets the session cookie
- `POST /auth/logout` clears the session cookie
- Protected frontend routes redirect unauthenticated users to `/login`

## Local Commands

Backend:

```bash
UTW_DATABASE_URL=... UTW_AUTH_SECRET_KEY=... uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token npm run dev
```

Smoke-validation dataset:

```bash
.venv/bin/python -m src.scripts.seed_smoke_validation_data
.venv/bin/python -m src.scripts.verify_smoke_validation_data
```

AI enrichment verification:

```bash
.venv/bin/python -m src.jobs.verify_enrich_recent_tenders_job
```

AWS runtime readiness verification:

```bash
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness
```

Optional live AWS probes:

```bash
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness --perform-bedrock-invoke
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness --perform-ses-send --ses-target-email you@example.com
```

## Production Checklist

- [ ] Database URL is configured and reachable
- [ ] Auth secret is present and long enough
- [ ] Production cookies are secure
- [ ] Cookie path and domain are set intentionally for the deployment topology
- [ ] `UTW_FRONTEND_BASE_URL` points to the deployed frontend base URL
- [ ] `UTW_CORS_ALLOW_ORIGINS` contains origin-only values and includes the deployed frontend origin
- [ ] `UTW_EMAIL_DELIVERY_BACKEND` is set to `ses`
- [ ] `UTW_EMAIL_SENDER` and `UTW_AWS_REGION` are set
- [ ] If AI is enabled, `UTW_AI_PROVIDER=bedrock_anthropic`
- [ ] If AI is enabled, Bedrock model IDs are configured explicitly and do not rely on Browser Use Cloud defaults
- [ ] If AI is enabled, the runtime has AWS IAM access to Bedrock and does not require `BROWSER_USE_API_KEY`
- [ ] If AI is enabled, `UTW_AI_DAILY_REQUEST_BUDGET` and `UTW_AI_DAILY_RESERVED_TOKEN_BUDGET` are set intentionally
- [ ] If AI is enabled, the runtime IAM role includes Bedrock `CountTokens` access in addition to invoke access
- [ ] `.venv/bin/python -m src.scripts.verify_aws_runtime_readiness` passes
- [ ] If AI is enabled, `--perform-bedrock-invoke` passes in the target environment
- [ ] If SES delivery is enabled, `--perform-ses-send --ses-target-email <approved address>` passes in the target environment
- [ ] If AI enrichment is enabled, failed summaries are bounded by `UTW_AI_SUMMARY_MAX_ATTEMPTS`
- [ ] If Browser Use agent runtime is enabled anywhere, `BROWSER_USE_REQUIRE_EXPLICIT_LLM=true`
- [ ] If Browser Use agent runtime is enabled anywhere, `DEFAULT_LLM` points at an explicit Bedrock model id
- [ ] Frontend build uses the correct public API URL and cookie name
- [ ] `npm run lint` passes
- [ ] `npm run typecheck` passes
- [ ] `npm run build` passes
- [ ] `/health/ready` returns `200`
- [ ] Login, logout, and protected page redirects work in the deployed environment
- [ ] A real email provider is configured for password-reset delivery before release
