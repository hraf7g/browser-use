# Terraform Baseline

This is the AWS production baseline for the current app runtime.

It provisions:

- VPC with public ALB subnets, private ECS app subnets, and isolated RDS subnets
- public ALB with ACM certificate and Route53 alias
- ECS/Fargate cluster and services for API and frontend
- dedicated ECS/Fargate browser-worker service for long-lived live browser runs
- ECR repositories for backend and frontend images
- PostgreSQL RDS instance
- Secrets Manager and SSM Parameter Store config required by the app
- EventBridge Scheduler jobs for crawling, enrichment, matching, and email dispatch
- IAM roles for ECS execution, ECS task runtime, and scheduler task launches
- CloudWatch log groups
- CloudWatch alarms, SNS alert topic, and a scheduler DLQ

## Inputs you still provide

- AWS credentials / account access
- image tags for backend and frontend
- domain and hosted zone
- SES sender identity
- initial operator email

The stack generates:

- PostgreSQL password
- application auth signing secret
- operator API key

## Remote state

Bootstrap a dedicated S3 bucket for Terraform state:

```bash
AWS_REGION=us-east-1 deploy/bin/aws-bootstrap-terraform-state.sh <state-bucket-name>
```

Then create a local backend config from [backend.hcl.example](/Users/achraf/Documents/browser-use/infra/terraform/backend.hcl.example:1):

```bash
cp infra/terraform/backend.hcl.example infra/terraform/backend.hcl
```

Update the bucket, key, and region values before running `terraform init`.

Generate a production tfvars file from environment variables:

```bash
export AWS_REGION=us-east-1
export DOMAIN_NAME=app.example.com
export HOSTED_ZONE_NAME=example.com
export SES_SENDER_EMAIL=tenders@example.com
export OPERATOR_EMAIL=operator@example.com
deploy/bin/aws-write-terraform-vars.sh <tag>
```

## Apply flow

1. Copy the example vars:

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
```

2. Update the values for your AWS account and environment.

3. Initialize and apply:

```bash
cd infra/terraform
terraform init -backend-config=backend.hcl
terraform plan
terraform apply
```

Or use the repo automation helpers:

```bash
deploy/bin/aws-write-terraform-vars.sh <tag>
deploy/bin/aws-bootstrap-ecr-repositories.sh <tag>   # first deploy only
deploy/bin/aws-build-push-images.sh <tag>
deploy/bin/aws-apply-infra.sh <tag>
```

## Image build and push

Build and push the images before or immediately after the first apply:

```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build -f deploy/docker/backend.Dockerfile -t <backend-repo>:<tag> .
docker push <backend-repo>:<tag>
docker build -f deploy/docker/frontend.Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=https://<domain> \
  --build-arg NEXT_PUBLIC_AUTH_COOKIE_NAME=utw_access_token \
  -t <frontend-repo>:<tag> .
docker push <frontend-repo>:<tag>
```

## Required one-off ECS tasks after first deploy

Run the backend task definition with these command overrides in order:

1. `["/app/deploy/bin/run-db-migrate.sh"]`
2. `["/app/deploy/bin/run-seed-sources.sh"]`
3. after the first real user account is created, `["/app/.venv/bin/python", "-m", "src.operator.promote_operator_user"]`

The third task requires `UTW_OPERATOR_EMAIL` to remain set in the backend runtime configuration.

You can run them with:

```bash
deploy/bin/aws-run-backend-task.sh migrate
deploy/bin/aws-run-backend-task.sh seed
deploy/bin/aws-run-backend-task.sh promote-operator
```

## Post-deploy smoke

After deployment, run:

```bash
deploy/bin/aws-post-deploy-smoke.sh
```

It verifies:

- the API, frontend, and browser-worker ECS services are stable
- `/`, `/health`, and `/health/ready` return success on the public domain
- the scheduler DLQ is empty

## Routing model

The ALB exposes one customer-facing domain:

- default route -> frontend
- API path prefixes like `/auth`, `/tenders`, `/operator`, `/health` -> backend

This keeps auth cookies same-origin and avoids frontend/backend CORS drift in production.

## Notes

- This baseline uses Multi-AZ RDS and one NAT gateway per AZ for production resilience.
- The backend task role includes Bedrock invoke/count permissions and SES send permissions because the current code uses both.
- The browser-worker runs as a dedicated ECS service so browser sessions and cancellation loops do not share failure domains with the API.
- EventBridge Scheduler jobs now send failed invocations to an SQS DLQ, and alarms watch target errors, dropped invocations, and visible DLQ messages.
- The task execution role can read the exact SSM parameters and Secrets Manager secrets provisioned by this stack.
- The Terraform state will contain generated secret values through `random_password`. Use an encrypted remote state backend before real production use.
- GitHub Actions production deploy uses AWS OIDC and a protected `production` environment. See [docs/aws-github-oidc.md](/Users/achraf/Documents/browser-use/docs/aws-github-oidc.md:1).
