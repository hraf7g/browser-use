# AWS Deployment v1: UAE Tender Watch (UTW)

## 1. Purpose

This document defines the recommended AWS deployment shape for UAE Tender Watch v1.

The deployment must optimize for:

- low operational burden
- low complexity
- acceptable reliability
- ability to run browser automation cleanly
- low waste of founder time

This is a solo-founder v1. The goal is not perfect cloud architecture. The goal is a setup that can be deployed, understood, monitored, and fixed without creating unnecessary infrastructure overhead.

---

## 2. Primary Recommendation

**Use one small EC2 instance for the application and crawler, plus one managed Postgres database, plus SES for email.**

This is the primary recommendation for v1.

Why this is the best fit:

- browser automation with Playwright/Chromium is easier on a normal Linux server than in more fragmented managed setups
- one application host is easier to understand and debug than splitting API and worker across multiple AWS services
- idle cost is easier to control
- deployment is simpler
- operations stay manageable for a solo founder

Recommended v1 stack:

- **EC2** — app host, API, frontend, scheduled worker execution
- **RDS PostgreSQL** — managed database
- **SES** — daily user emails and founder alerts
- **Secrets Manager** or **SSM Parameter Store** — secrets storage
- **CloudWatch** — logs and basic alarms

---

## 3. Why Not the Heavier Managed Stack

A more fragmented stack like:

- App Runner
- Fargate
- EventBridge
- RDS
- CloudWatch
- SES

can work, but it is heavier than necessary for v1.

Problems with that shape for this product:

- more moving parts to configure
- more deployment surfaces to debug
- more AWS-specific networking complexity
- browser automation runtime becomes less straightforward
- higher cognitive load for a solo founder

For a small product with 2 daily crawls, the extra separation does not buy enough value yet.

---

## 4. v1 Infrastructure Components

## 4.1 EC2 Application Host

Use one small Linux EC2 instance as the main application host.

Responsibilities:

- serve backend API
- serve web frontend
- run scheduled crawler jobs
- run matching job
- run daily email job
- write application logs

Why EC2 is appropriate here:

- simplest place to run browser automation reliably
- easiest to SSH into when something breaks
- avoids container orchestration overhead
- keeps app and worker close together for v1

Suggested starting size:
- start small but practical
- enough memory for Chromium plus app runtime
- final size can be chosen during implementation/testing based on actual browser memory usage

The exact instance type can be finalized later, but it should favor:
- stable RAM
- low monthly idle cost
- simple Linux compatibility

---

## 4.2 RDS PostgreSQL

Use managed PostgreSQL on RDS.

Responsibilities:

- store users
- store keyword profiles
- store sources
- store tenders
- store matches
- store crawl run state
- store email delivery state

Why RDS is worth it even in v1:

- managed backups
- easier recovery than self-hosted database
- less operational risk than running Postgres inside EC2
- simpler long-term migration path

This is the one place where managed service value is clearly worth the extra cost.

---

## 4.3 SES

Use Amazon SES for email.

Responsibilities:

- send daily user brief
- send founder failure alerts

Why SES:

- native AWS option
- low cost
- good fit for transactional email
- enough for v1

Do not overdesign email in v1.
You only need reliable outbound email and minimal delivery tracking.

---

## 4.4 Secrets Storage

Use one of these, with a preference for the simpler one if cost/control matters:

- **SSM Parameter Store** for leaner v1 secrets handling
- **Secrets Manager** if you want stronger managed secret rotation and a more formal secrets workflow

For v1, either is acceptable, but the deployment should choose **one** and stick to it.

Recommended default for lean v1:
**SSM Parameter Store**

Store:

- database URL or DB credentials
- session/auth secrets
- email credentials/config
- AI provider credentials if used
- any portal configuration that should not live in code

---

## 4.5 CloudWatch

Use CloudWatch for:

- application logs
- crawler logs
- basic alerting

You do not need a large monitoring setup in v1.

What to log:

- crawl start
- crawl success/failure
- source name
- run identifier
- tenders added
- matching results count
- email send success/failure

Useful alarms in v1:

- repeated crawl failure
- app process not healthy
- disk pressure if needed
- instance health issues

---

## 5. Deployment Shape

The recommended v1 runtime shape is:

### On EC2
- backend API process
- frontend-serving process
- scheduler or cron-based job trigger
- crawler execution process
- matching job
- daily email job

### On RDS
- PostgreSQL only

### On SES
- transactional outbound email only

### On CloudWatch
- log collection
- a few basic alarms

This keeps the whole product understandable.

---

## 6. Scheduling Approach

For v1, use a simple scheduler on the EC2 host.

Examples:
- system cron
- a small application scheduler
- a process supervisor plus scheduled task runner

The goal is not fancy orchestration.
The goal is reliable daily execution.

Recommended pattern:

- early daily crawl for Source A
- then Source B
- then matching
- then daily email
- founder alert immediately on crawl failure

No external orchestration service is required yet.

---

## 7. App and Worker Layout

v1 should run application and worker logic on the same EC2 host, but as separate processes.

Why:

- simpler deployment
- simpler logging
- easier debugging
- no distributed coordination problem

Important boundary:
- same machine is fine
- same process is not required

Keep the crawler worker isolated in code and process model even if it shares the same host.

---

## 8. Frontend Hosting

Serve the frontend from the same app host in v1.

That means:

- no separate S3/CloudFront frontend stack yet
- no split hosting unless implementation genuinely requires it

This reduces:
- DNS complexity
- deployment complexity
- cross-origin issues
- mental overhead

For v1, one app host is the right tradeoff.

---

## 9. Networking

Keep networking simple.

Recommended posture:

- EC2 host accessible only as needed for the app
- RDS not publicly exposed
- security group rules restricted to what the app needs
- SSH access restricted tightly

Avoid unnecessary complexity like:
- NAT gateways
- complex private subnet patterns
- multi-AZ networking design
- service mesh style thinking

Those are not needed for a 2-source browser automation MVP.

---

## 10. Backups and Recovery

## Database
Use RDS automated backups.

This is mandatory.

## Application host
Keep the app deployable from source and configuration.
Do not rely on the EC2 disk as the only copy of anything important.

Practical rule:
- code lives in repo
- secrets live in AWS secret storage
- data lives in RDS
- logs flow to CloudWatch

That way, if the EC2 instance dies, you can recreate it.

---

## 11. Cost Philosophy

v1 should optimize for:

- low idle spend
- low setup cost
- low debugging cost
- low founder time cost

It is acceptable if this is not the absolute cheapest possible AWS bill.
The bigger danger is wasting weeks on avoidable infrastructure complexity.

The recommended EC2 + RDS + SES shape is usually the best tradeoff for that.

---

## 12. Security Baseline

Minimum security posture for v1:

- no public database
- restricted SSH access
- secrets not committed to repo
- HTTPS on the app
- least-privilege AWS credentials where practical
- separate app config for production

Do not try to build enterprise security architecture in v1.
Just avoid obvious mistakes.

---

## 13. Tradeoffs

## Pros of this recommendation
- simpler than multi-service serverless/container stack
- easier browser automation runtime
- easier debugging
- fewer AWS services to misconfigure
- realistic for a solo founder

## Cons of this recommendation
- one EC2 host is a single app-host failure point
- less elegant scaling story
- more manual server ownership than App Runner/Fargate
- some OS-level maintenance still exists

These tradeoffs are acceptable in v1 because the product is small and the workload is low.

---

## 14. When to Revisit This Architecture

You should reconsider the deployment shape only if one of these becomes true:

- crawl workload increases significantly
- you add many more sources
- browser jobs become too heavy for one host
- uptime requirements increase materially
- deployment frequency and team size grow
- the product proves demand and can justify more infrastructure effort

Until then, keep it simple.

---

## 15. Final Recommendation

For UAE Tender Watch v1, deploy on:

- **one EC2 app/worker host**
- **one RDS PostgreSQL database**
- **SES for email**
- **SSM Parameter Store or Secrets Manager for secrets**
- **CloudWatch for logs and basic alarms**

That is the most realistic AWS setup for a lean, production-aware, solo-founder first version.