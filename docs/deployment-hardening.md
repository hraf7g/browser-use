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

Frontend:

- `NEXT_PUBLIC_API_URL=https://api.example.com`
- `NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token`

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

## Production Checklist

- [ ] Database URL is configured and reachable
- [ ] Auth secret is present and long enough
- [ ] Production cookies are secure
- [ ] Cookie path and domain are set intentionally for the deployment topology
- [ ] CORS only allows the deployed frontend origins
- [ ] Frontend build uses the correct public API URL
- [ ] `npm run lint` passes
- [ ] `npm run typecheck` passes
- [ ] `npm run build` passes
- [ ] `/health/ready` returns `200`
- [ ] Login, logout, and protected page redirects work in the deployed environment
