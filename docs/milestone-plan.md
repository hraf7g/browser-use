
# Milestone Plan: UAE Tender Watch (UTW) v1

## 1. Purpose

This document defines the milestone-based build plan for UTW v1.

The milestone order is designed to:

- prove the product loop early
- delay fragile crawler work until later
- keep infrastructure and implementation lean
- align with the chosen v1 architecture

---

## 2. Milestone 0: Project Scaffolding

### Goal
Create a runnable local application shell.

### Deliverables
- `src/` folder structure created
- config loading set up
- local app run command works
- health endpoint implemented
- basic logging initialized

### Done when
- app starts locally
- `GET /health` returns `200`
- config loads cleanly in local environment

### Exclusions
- database models
- auth
- crawler code
- email sending

### Main risks
- environment/tooling mismatch
- poor early project structure decisions

---

## 3. Milestone 1: Database, Models, and Seed Data

### Goal
Establish the source of truth for application data.

### Deliverables
- models implemented from `docs/data-model.md`
- migration setup works
- initial migration created
- exactly 2 source records seeded
- manual tender insertion path works through app data layer

### Done when
- schema can be created from scratch
- seeded sources exist
- one manual tender can be inserted successfully through the intended ingestion path

### Exclusions
- auth
- matching
- crawler integration
- production email

### Main risks
- schema mismatch
- weak dedupe design
- migration drift

---

## 4. Milestone 2: Auth, Keyword Profile, and Minimal Tenders List

### Goal
Make the app usable for a real user with manually inserted data.

### Deliverables
- signup endpoint
- login endpoint
- token auth working
- current user endpoint
- keyword profile read/update endpoints
- `GET /tenders` endpoint
- minimal tenders list UI/page

### Done when
- user can sign up
- user can log in
- user can save keyword profile
- user can view manually inserted tenders in the app

### Exclusions
- matching
- email generation
- crawler code
- operator status

### Main risks
- auth implementation mistakes
- validation inconsistency
- UI/API mismatch

---

## 5. Milestone 3: Ingestion, Matching, and Dummy Email Vertical Slice

### Goal
Prove the core product loop without crawler dependency.

### Deliverables
- shared ingestion layer implemented
- dedupe behavior tested
- matching logic implemented
- local/dev email backend implemented
- daily brief generation logic implemented

### Done when
- a manually inserted tender is ingested correctly
- a matching user gets a generated local/dev daily brief
- duplicate match and duplicate alert rules are verified

### Exclusions
- live crawler integration
- SES
- AI summarization

### Main risks
- broken dedupe logic
- duplicate alerts
- weak email state handling

---

## 6. Milestone 4: Operator Status and First Crawler Source

### Goal
Introduce the first real source safely.

### Deliverables
- crawl run tracking
- source status updates
- operator status endpoint/page
- first source crawler implementation
- fixture-based crawler tests
- manual live validation against the first source

### Done when
- first source crawler works against fixture data
- first source crawler is manually validated against the live portal
- new tenders from source 1 can be persisted through ingestion
- operator status reflects source run state correctly

### Exclusions
- second source
- SES
- AI summarization

### Main risks
- live portal instability
- selector fragility
- mismatch between fixture tests and live portal behavior

---

## 7. Milestone 5: Second Crawler Source

### Goal
Expand from one source to two without breaking the core loop.

### Deliverables
- second source crawler implementation
- fixture-based tests for source 2
- manual live validation against source 2
- multi-source run stability checks

### Done when
- second source crawler works against fixture data
- second source crawler is manually validated against the live portal
- both sources can be run and persist records through the same ingestion path

### Exclusions
- SES
- AI summarization
- deployment hardening

### Main risks
- second source access issues
- differing source structure
- duplicated crawler logic

---

## 8. Milestone 6: Optional AI Enrichment and SES Integration

### Goal
Add production delivery and secondary enrichment.

### Deliverables
- optional AI summary flow for persisted tenders
- SES email backend
- founder failure alert email path
- production email configuration

### Done when
- AI summary runs only after successful persistence
- a real daily brief can be sent through SES
- founder receives failure alert on crawl/persistence failure
- product still works if AI enrichment is disabled

### Exclusions
- instant notifications
- billing
- advanced analytics

### Main risks
- SES setup friction
- AI cost/latency
- AI failure affecting main flow if boundaries are not respected

---

## 9. Milestone 7: Hardening and Deployment Readiness

### Goal
Prepare the product for first production use.

### Deliverables
- production config validation
- deployment scripts/config for lean AWS target
- logging and failure alert verification
- secure secret handling
- one full scheduled cycle tested in deployed environment

### Done when
- app is deployed on the chosen lean AWS setup
- one complete scheduled crawl/match/email cycle succeeds
- logs and founder alerts are visible and usable
- deployment can be repeated cleanly

### Exclusions
- autoscaling
- multi-region
- enterprise ops tooling

### Main risks
- production config mismatch
- deployment drift
- cloud email or crawler runtime surprises

---

## 10. Final Build Principle

The milestone order must remain:

1. app shell
2. DB and models
3. user/auth/profile/tenders read path
4. ingestion + matching + dummy email
5. first crawler
6. second crawler
7. AI + SES
8. hardening and deployment

That is the correct order for shipping a production-aware v1 without wasting time on the most fragile layer too early.