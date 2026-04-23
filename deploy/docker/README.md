# Container Images

These Dockerfiles are the production application images for AWS ECS/Fargate.

## Images

- `backend.Dockerfile`: FastAPI API plus crawler/job runtime
- `frontend.Dockerfile`: Next.js production runtime

## Backend Image

Build:

```bash
docker build -f deploy/docker/backend.Dockerfile -t utw-backend:local .
```

Default container command:

```bash
python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
```

One-off ECS task command overrides should use the scripts under `deploy/bin`, for example:

- `deploy/bin/run-db-migrate.sh`
- `deploy/bin/run-seed-sources.sh`
- `deploy/bin/run-all-sources.sh`
- `deploy/bin/run-enrich-recent.sh`
- `deploy/bin/run-match-recent.sh`
- `deploy/bin/run-send-pending-daily-briefs.sh`
- `deploy/bin/run-send-pending-instant-alerts.sh`

The backend image intentionally includes Chromium because scheduled crawler and enrichment tasks reuse the same image.

## Frontend Image

Build:

```bash
docker build \
  -f deploy/docker/frontend.Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=https://api.example.com \
  --build-arg NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token \
  -t utw-frontend:local \
  .
```

Important:

- `NEXT_PUBLIC_*` values are compiled into the frontend build.
- A separate image should be built per environment if those values differ.
- The runtime container does not need `npm`, source files, or dev dependencies.

## ECS Mapping

Recommended ECS services/tasks:

- `utw-api` ECS service from backend image
- `utw-frontend` ECS service from frontend image
- `utw-browser-worker` ECS service from backend image for continuous browser-agent execution
- scheduled ECS tasks from backend image for crawler/matching/enrichment/email jobs
- one-off ECS tasks from backend image for DB migration and source seeding
