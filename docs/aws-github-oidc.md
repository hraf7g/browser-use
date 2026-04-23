# AWS GitHub OIDC Setup

Use GitHub Actions OIDC for AWS access instead of long-lived IAM user keys.

Official references used for this setup:

- AWS: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_oidc.html
- GitHub: https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-aws
- Terraform S3 backend: https://developer.hashicorp.com/terraform/language/settings/backends/s3

## What to create in AWS

1. Add GitHub's OIDC provider to IAM:
   - provider URL: `https://token.actions.githubusercontent.com`
   - audience: `sts.amazonaws.com`

2. Create a deploy role for this repo.

Recommended trust policy template:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:<OWNER>/<REPO>:ref:refs/heads/main",
            "repo:<OWNER>/<REPO>:environment:production"
          ]
        }
      }
    }
  ]
}
```

3. Attach policies that allow:
   - Terraform-managed AWS resources in `infra/terraform`
   - ECR push/pull
   - ECS deploy/run-task/wait
   - Route53, ACM, ALB, RDS, IAM, SSM, Secrets Manager, EventBridge Scheduler, CloudWatch, SNS, SQS
   - S3 access to the Terraform state bucket

## GitHub repository variables

Set these repository or environment variables:

- `AWS_REGION`
- `AWS_ROLE_TO_ASSUME`
- `TF_STATE_BUCKET`
- `TF_STATE_KEY`
- `DOMAIN_NAME`
- `HOSTED_ZONE_NAME`
- `SES_SENDER_EMAIL`
- `OPERATOR_EMAIL`

Optional:

- `TF_STATE_REGION`
- `APP_URL`
- `ALARM_EMAIL_ENDPOINT`

Recommended values:

- `TF_STATE_KEY=utw/production/terraform.tfstate`
- `TF_STATE_REGION=<same as AWS_REGION>`

## GitHub environment

Create a protected environment named `production` and put the deploy workflow there.

Recommended protections:

- required reviewers
- branch restriction to `main`
- manual approval before deployment

## Terraform state note

This repo uses the S3 backend `use_lockfile = true` pattern instead of DynamoDB locking.
That matches current HashiCorp guidance for the S3 backend.
