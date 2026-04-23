# Production Deployment Assets

This directory contains the application-side deployment assets for an EC2-based AWS deployment.

Container packaging for ECS/Fargate also lives here:

- [deploy/docker/README.md](/Users/achraf/Documents/browser-use/deploy/docker/README.md:1)
- [deploy/docker/backend.Dockerfile](/Users/achraf/Documents/browser-use/deploy/docker/backend.Dockerfile:1)
- [deploy/docker/frontend.Dockerfile](/Users/achraf/Documents/browser-use/deploy/docker/frontend.Dockerfile:1)

AWS infrastructure as code now lives under [infra/terraform/README.md](/Users/achraf/Documents/browser-use/infra/terraform/README.md:1).

AWS release automation scripts now live in `deploy/bin`:

- `aws-build-push-images.sh`
- `aws-bootstrap-terraform-state.sh`
- `aws-bootstrap-ecr-repositories.sh`
- `aws-write-terraform-vars.sh`
- `aws-apply-infra.sh`
- `aws-force-new-deployment.sh`
- `aws-run-backend-task.sh`
- `aws-post-deploy-smoke.sh`

## Assumptions

- Application checkout lives at `/opt/utw/current`
- Backend environment file lives at `/etc/utw/backend.env`
- Frontend environment file lives at `/etc/utw/frontend.env`
- A Python virtualenv exists at `/opt/utw/current/.venv`
- Frontend dependencies are installed in `/opt/utw/current/frontend`
- Reverse proxy and TLS termination are handled separately, typically with `nginx`

## Secret Handling

- Do not store production secrets inside the repo checkout.
- Do not write secrets into `.venv` or any file under `.venv`.
- Keep runtime env files outside the repo at `/etc/utw/backend.env` and `/etc/utw/frontend.env`.
- On AWS, prefer SSM Parameter Store or Secrets Manager and render/inject those values at deploy time.

## Services

- `utw-api.service`: FastAPI backend via `uvicorn`
- `utw-frontend.service`: Next.js frontend via `next start`

For ECS/Fargate, use the container commands in [deploy/docker/README.md](/Users/achraf/Documents/browser-use/deploy/docker/README.md:1) and the scripts in `deploy/bin`.

For live browser-agent execution, run the worker command in a dedicated long-lived process or ECS service:

- `deploy/bin/run-browser-agent-worker.sh`

That worker should not share the API service process. In AWS, run it as a dedicated ECS service so browser sessions, cancellation handling, and worker restarts stay isolated from the customer-facing API.

## Scheduled Jobs

- `utw-run-all-sources.timer`: runs all crawlers once per day
- `utw-match-recent.timer`: matches newly crawled tenders every hour
- `utw-send-pending-daily-briefs.timer`: sends daily digests once per day
- `utw-send-pending-instant-alerts.timer`: flushes queued instant alerts every 15 minutes

## First Deploy Sequence

1. Sync code and install backend/frontend dependencies.
2. Populate `/etc/utw/backend.env` and `/etc/utw/frontend.env`.
   Use [backend.env.template](/Users/achraf/Documents/browser-use/deploy/backend.env.template:1), [frontend.env.template](/Users/achraf/Documents/browser-use/deploy/frontend.env.template:1), and [aws-secret-matrix.md](/Users/achraf/Documents/browser-use/docs/aws-secret-matrix.md:1).
3. Run Alembic migrations.
4. Seed canonical monitored sources.
5. Build the Next.js frontend.
6. Enable and start the systemd units and timers.

## Example Backend Env Additions

```env
UTW_ENVIRONMENT=production
UTW_DATABASE_URL=postgresql+psycopg://...
UTW_AUTH_SECRET_KEY=...
UTW_AUTH_COOKIE_SECURE=true
UTW_CORS_ALLOW_ORIGINS=https://app.example.com
UTW_FRONTEND_BASE_URL=https://app.example.com
UTW_EMAIL_DELIVERY_BACKEND=ses
UTW_EMAIL_SENDER=alerts@example.com
UTW_AWS_REGION=us-east-1
```

## Example Frontend Env

```env
NODE_ENV=production
PORT=3000
HOSTNAME=127.0.0.1
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token
```
