# Next Phase Guide

This file is the practical, beginner-friendly guide for what to do next.

It covers:

- what still needs to be implemented
- what to test before production
- exact terminal commands for local backend and frontend work
- exact terminal commands for repo validation
- what AWS services/tools you need
- how to connect the app to real AI on AWS
- how to deploy the app to AWS
- how to attach a real domain name

This guide is written for someone who wants one place to follow, step by step.

## 1. Where The Project Stands Right Now

The backend is in much better shape than before. The recent hardening work already improved:

- route validation so bad input does not leak `500` errors
- auth side-effect ordering so partial success is less likely
- browser-agent worker admission under concurrency
- operator access and operator audit logging
- advisory-lock handling so successful jobs are not falsely marked as failed
- AWS readiness instrumentation for Bedrock, SES, and runtime checks

That means the project is no longer in "prototype only" shape. It is now in "prepare for real deployment" shape.

What is still missing is mostly deployment completion, operational readiness, and end-to-end production verification.

## 2. What Needs To Be Implemented Next

These are the next real deliverables.

### A. Finish Production Readiness On The App Side

Implement or verify all of the following:

- real operator workflows using authenticated operator users in production
- end-to-end login, logout, password reset, and protected route behavior on the deployed domain
- production email delivery verification with Amazon SES
- production AI verification with Amazon Bedrock
- migration and seed flow in AWS after first deploy
- source crawler execution in deployed environment
- scheduled jobs in deployed environment
- browser worker service in deployed environment
- post-deploy smoke checks against the real domain
- alerting and dashboards for failures

### B. Add Remaining Production Tests

Recommended next tests to add:

- deployed-domain auth flow smoke test
- real operator session smoke test
- browser-agent run queue smoke test in deployed environment
- scheduler smoke test for crawl, match, enrich, daily brief, and instant alerts
- SES send smoke test against an approved recipient
- Bedrock invoke smoke test against the real configured model
- database migration smoke test

### C. Finish Operational Tooling

Recommended next operational improvements:

- CloudWatch dashboard for API, worker, scheduler, and DLQ
- CloudWatch alarms for 5xx rates, ECS restarts, DLQ growth, and RDS health
- log filters for `operator_action`, `job_lock_release_failed`, and `password_reset_email_dispatch_failed`
- runbooks for "API down", "worker stuck", "scheduler DLQ non-zero", "Bedrock access denied", and "SES send failure"

## 3. Local Development Setup

Run these commands from the repo root:

```bash
cd /Users/achraf/Documents/browser-use
uv venv --python 3.11
source .venv/bin/activate
uv sync --dev --all-extras
```

If you have not created your local `.env` yet:

```bash
cp .env.example .env
```

Then edit `.env` with local values.

## 4. Commands To Run The Backend Locally

Start the backend:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Alternative command from the project docs:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
UTW_DATABASE_URL=... UTW_AUTH_SECRET_KEY=... uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Backend health checks:

```bash
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/health/ready
```

## 5. Commands To Run The Frontend Locally

Start the frontend:

```bash
cd /Users/achraf/Documents/browser-use/frontend
npm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token npm run dev
```

Standard frontend commands:

```bash
cd /Users/achraf/Documents/browser-use/frontend
npm run lint
npm run typecheck
npm run build
npm run start
```

## 6. Commands To Run The Worker And Jobs Locally

Run the browser worker:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
./deploy/bin/run-browser-agent-worker.sh
```

Run one-off jobs:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
./deploy/bin/run-db-migrate.sh
./deploy/bin/run-seed-sources.sh
./deploy/bin/run-all-sources.sh
./deploy/bin/run-match-recent.sh
./deploy/bin/run-enrich-recent.sh
./deploy/bin/run-send-pending-daily-briefs.sh
./deploy/bin/run-send-pending-instant-alerts.sh
```

## 7. Commands To Validate The Repo Before Deploying

Run targeted backend tests:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
uv run pytest tests
```

Run the browser-use CI-style suite if needed:

```bash
cd /Users/achraf/Documents/browser-use
./bin/test.sh
```

Run lint and formatting checks:

```bash
cd /Users/achraf/Documents/browser-use
./bin/lint.sh
```

Run the smoke validation dataset flow:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
.venv/bin/python -m src.scripts.seed_smoke_validation_data
.venv/bin/python -m src.scripts.verify_smoke_validation_data
```

Run AI enrichment verification:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
.venv/bin/python -m src.jobs.verify_enrich_recent_tenders_job
```

Run AWS readiness verification without live calls:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness
```

Run optional live Bedrock and SES probes later, after AWS credentials are ready:

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness --perform-bedrock-invoke
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness --perform-ses-send --ses-target-email you@example.com
```

## 8. AWS Services And Tools You Should Add

These are the AWS tools and services you should use for a real deployment.

### Required AWS Services

- `Route 53`
  Use for DNS and hosted zone management.

- `ACM (AWS Certificate Manager)`
  Use for HTTPS/TLS certificates.

- `ALB (Application Load Balancer)`
  Use to route traffic to frontend and backend.

- `ECR (Elastic Container Registry)`
  Use to store backend and frontend Docker images.

- `ECS Fargate`
  Use to run:
  - API service
  - frontend service
  - browser worker service
  - scheduled backend tasks

- `RDS PostgreSQL`
  Use as the production database.

- `Secrets Manager`
  Use for:
  - `UTW_DATABASE_URL`
  - `UTW_AUTH_SECRET_KEY`
  - `UTW_OPERATOR_API_KEY`

- `SSM Parameter Store`
  Use for non-secret production config.

- `IAM`
  Use for ECS task roles, execution roles, scheduler roles, and GitHub deployment role.

- `CloudWatch`
  Use for logs, alarms, and dashboards.

- `EventBridge Scheduler`
  Use for recurring jobs:
  - crawl
  - match
  - enrich
  - daily briefs
  - instant alerts

- `SQS`
  Use as the scheduler DLQ.

- `SNS`
  Use for alarm notifications.

### Recommended AWS Extras

- `WAF`
  Recommended in front of the ALB for production hardening.

- `CloudTrail`
  Recommended for AWS audit trail.

- `AWS Budgets`
  Recommended for cost alerts, especially once Bedrock is live.

## 9. Local Tools You Need Installed On Your Machine

Install these before attempting AWS deployment:

- `uv`
- `python 3.11`
- `node` and `npm`
- `docker`
- `aws cli`
- `terraform`
- `git`
- optional: `jq`

Quick checks:

```bash
uv --version
python3 --version
node --version
npm --version
docker --version
aws --version
terraform --version
git --version
```

## 10. Real AI Setup On AWS

This project is designed to use Amazon Bedrock instead of Browser Use Cloud defaults.

### What You Need

You need:

- a real AWS account
- AWS IAM permissions for Bedrock
- the correct AWS region
- the Bedrock models enabled in that account/region

### Bedrock Permissions Needed

Your runtime role must allow:

- Bedrock model invoke
- Bedrock `CountTokens`

This is important because the app uses token estimation before invoking.

### App Environment Variables For Real AI

Set these in AWS runtime config:

```env
UTW_AI_PROVIDER=bedrock_anthropic
UTW_AI_MODEL=anthropic.claude-sonnet-4-6
UTW_AI_FALLBACK_MODEL=anthropic.claude-haiku-4-5
UTW_AI_BEDROCK_USE_AMBIENT_CREDENTIALS=true
UTW_AWS_REGION=us-east-1
UTW_AI_MAX_TOKENS=8192
UTW_AI_TEMPERATURE=0.0
UTW_AI_SUMMARY_BATCH_SIZE=25
UTW_AI_SUMMARY_MAX_ATTEMPTS=3
UTW_AI_DAILY_REQUEST_BUDGET=500
UTW_AI_DAILY_RESERVED_TOKEN_BUDGET=200000
BROWSER_USE_REQUIRE_EXPLICIT_LLM=true
DEFAULT_LLM=bedrock_anthropic:us.anthropic.claude-sonnet-4-20250514-v1:0
BROWSER_USE_AWS_REGION=us-east-1
```

### Real AI Verification Commands

Run this first:

```bash
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness
```

Then run the live Bedrock probe:

```bash
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness --perform-bedrock-invoke
```

If that fails, do not continue to production traffic until it passes.

## 11. Real Email Setup On AWS

This project uses Amazon SES for production email.

### What You Need

You need:

- a verified SES sender identity
- correct region
- production SES access if your account is still in sandbox
- optional configuration set

### App Environment Variables For SES

```env
UTW_EMAIL_DELIVERY_BACKEND=ses
UTW_EMAIL_SENDER=alerts@example.com
UTW_EMAIL_REPLY_TO=
UTW_EMAIL_SES_CONFIGURATION_SET=
UTW_EMAIL_SES_FROM_ARN=
UTW_AWS_REGION=us-east-1
```

### SES Verification Commands

Run this first:

```bash
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness
```

Then run a live SES test:

```bash
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness --perform-ses-send --ses-target-email you@example.com
```

If this fails, password reset and notifications are not production-ready.

## 12. Step-By-Step AWS Deployment Plan

This is the clean path.

### Step 1. Prepare AWS Account

Do this first:

- create or access your AWS account
- choose the production region
- make sure Bedrock is enabled in that region
- verify your SES sender identity
- create or confirm your Route 53 hosted zone

### Step 2. Prepare Terraform State

Bootstrap Terraform state bucket:

```bash
cd /Users/achraf/Documents/browser-use
AWS_REGION=us-east-1 deploy/bin/aws-bootstrap-terraform-state.sh <state-bucket-name>
```

Create Terraform backend config:

```bash
cp infra/terraform/backend.hcl.example infra/terraform/backend.hcl
```

Edit `infra/terraform/backend.hcl` and set:

- S3 bucket
- key
- region

### Step 3. Set Deployment Environment Variables

Export the minimum values:

```bash
export AWS_REGION=us-east-1
export DOMAIN_NAME=app.example.com
export HOSTED_ZONE_NAME=example.com
export SES_SENDER_EMAIL=alerts@example.com
export OPERATOR_EMAIL=operator@example.com
```

Generate Terraform variables:

```bash
deploy/bin/aws-write-terraform-vars.sh <tag>
```

### Step 4. Bootstrap ECR Repositories

First deploy only:

```bash
deploy/bin/aws-bootstrap-ecr-repositories.sh <tag>
```

### Step 5. Build And Push Images

Use repo automation:

```bash
deploy/bin/aws-build-push-images.sh <tag>
```

Or manually:

```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com

docker build -f deploy/docker/backend.Dockerfile -t <backend-repo>:<tag> .
docker push <backend-repo>:<tag>

docker build -f deploy/docker/frontend.Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=https://app.example.com \
  --build-arg NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token \
  -t <frontend-repo>:<tag> .
docker push <frontend-repo>:<tag>
```

### Step 6. Apply Infrastructure

Using repo automation:

```bash
deploy/bin/aws-apply-infra.sh <tag>
```

Or manually:

```bash
cd infra/terraform
terraform init -backend-config=backend.hcl
terraform plan
terraform apply
```

### Step 7. Run One-Off Backend Tasks

After first deploy, run these in order:

```bash
deploy/bin/aws-run-backend-task.sh migrate
deploy/bin/aws-run-backend-task.sh seed
deploy/bin/aws-run-backend-task.sh promote-operator
```

These correspond to:

1. database migrations
2. source seeding
3. promoting the initial operator user

### Step 8. Run Post-Deploy Smoke

After services are up:

```bash
deploy/bin/aws-post-deploy-smoke.sh
```

### Step 9. Run AWS Runtime Readiness Checks In The Deployed Environment

Run:

```bash
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness --perform-bedrock-invoke
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness --perform-ses-send --ses-target-email you@example.com
```

### Step 10. Run User-Facing Smoke Tests

Manually verify:

- open the real site
- sign up or log in
- log out
- password reset request
- tenders list loads
- notification preferences load
- operator route works for operator session

## 13. Domain Name Setup Step By Step

Use this exact sequence.

### Step 1. Buy Or Choose A Domain

Example:

- `example.com`
- `mycompany.com`

### Step 2. Create A Hosted Zone In Route 53

Create the hosted zone for the root domain:

- `example.com`

### Step 3. Decide The Public URLs

Recommended:

- frontend: `https://app.example.com`
- API: same origin through ALB path routing

This repo is already designed for a same-origin routing model in production.

That means:

- frontend on the domain root/default route
- API on `/auth`, `/tenders`, `/operator`, `/health`, etc.

This reduces cookie and CORS problems.

### Step 4. Request TLS Certificate In ACM

Request a certificate for:

- `app.example.com`

Or for both:

- `example.com`
- `app.example.com`

Validate it using Route 53.

### Step 5. Point The Domain To The ALB

Terraform in this repo already expects:

- hosted zone
- certificate
- ALB alias

After apply, confirm DNS resolves and HTTPS works.

### Step 6. Match App Configuration To The Domain

Backend production config:

```env
UTW_FRONTEND_BASE_URL=https://app.example.com
UTW_CORS_ALLOW_ORIGINS=https://app.example.com
UTW_AUTH_COOKIE_SECURE=true
UTW_AUTH_COOKIE_PATH=/
UTW_AUTH_COOKIE_SAME_SITE=lax
```

Frontend production config:

```env
NEXT_PUBLIC_API_URL=https://app.example.com
NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token
```

## 14. Recommended Production Environment Layout

### Backend Runtime

Use values based on:

- `deploy/backend.env.template`
- `docs/aws-secret-matrix.md`

### Frontend Runtime

Use values based on:

- `deploy/frontend.env.template`

### Important Rule

Do not put production secrets in:

- `.env`
- the repo
- `.venv`

Use:

- `Secrets Manager` for secrets
- `SSM Parameter Store` for non-secret runtime config

## 15. Practical Checklist Before Go-Live

Do not go live until all of these are true.

- backend starts cleanly in AWS
- frontend starts cleanly in AWS
- browser worker service is running
- migrations completed
- sources seeded
- Bedrock readiness check passes
- SES readiness check passes
- `/health` passes
- `/health/ready` passes
- post-deploy smoke passes
- scheduler DLQ is empty
- login works
- logout works
- password reset works
- operator access works
- one real crawl run works
- one real match run works
- one real enrichment run works
- one real email flow works

## 16. Suggested Order Of Execution

If you want the shortest safe path, follow this exact order:

1. Finish local validation.
2. Run backend tests and lint.
3. Run frontend lint, typecheck, and build.
4. Prepare AWS account, domain, SES, and Bedrock.
5. Bootstrap Terraform state.
6. Generate Terraform vars.
7. Bootstrap ECR.
8. Build and push images.
9. Apply infra.
10. Run migrate task.
11. Run seed task.
12. Promote operator user.
13. Run post-deploy smoke.
14. Run AWS runtime readiness checks.
15. Test login, logout, password reset, operator access.
16. Run one real crawl and matching cycle.
17. Run one real AI check.
18. Run one real SES send.
19. Only then treat the deployment as production-ready.

## 17. Copy-Paste Command Block For Local Work

```bash
cd /Users/achraf/Documents/browser-use
uv venv --python 3.11
source .venv/bin/activate
uv sync --dev --all-extras
cp .env.example .env
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal:

```bash
cd /Users/achraf/Documents/browser-use/frontend
npm install
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000 NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token npm run dev
```

## 18. Copy-Paste Command Block For Pre-Deploy Validation

```bash
cd /Users/achraf/Documents/browser-use
source .venv/bin/activate
uv run pytest tests
./bin/lint.sh
cd frontend
npm run lint
npm run typecheck
npm run build
cd ..
.venv/bin/python -m src.scripts.seed_smoke_validation_data
.venv/bin/python -m src.scripts.verify_smoke_validation_data
.venv/bin/python -m src.scripts.verify_aws_runtime_readiness
```

## 19. Copy-Paste Command Block For AWS Deployment

```bash
cd /Users/achraf/Documents/browser-use
export AWS_REGION=us-east-1
export DOMAIN_NAME=app.example.com
export HOSTED_ZONE_NAME=example.com
export SES_SENDER_EMAIL=alerts@example.com
export OPERATOR_EMAIL=operator@example.com

AWS_REGION=us-east-1 deploy/bin/aws-bootstrap-terraform-state.sh <state-bucket-name>
cp infra/terraform/backend.hcl.example infra/terraform/backend.hcl
deploy/bin/aws-write-terraform-vars.sh <tag>
deploy/bin/aws-bootstrap-ecr-repositories.sh <tag>
deploy/bin/aws-build-push-images.sh <tag>
deploy/bin/aws-apply-infra.sh <tag>
deploy/bin/aws-run-backend-task.sh migrate
deploy/bin/aws-run-backend-task.sh seed
deploy/bin/aws-run-backend-task.sh promote-operator
deploy/bin/aws-post-deploy-smoke.sh
```

## 20. Final Recommendation

Do not rush straight from "tests pass locally" to "production is ready".

The correct production-grade mindset for this repo is:

- validate locally
- validate deployed infrastructure
- validate real AWS dependencies
- validate real domain and auth behavior
- validate one complete user journey

Only after all of those pass should you treat the system as ready for real users.
