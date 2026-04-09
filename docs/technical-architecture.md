# Technical Architecture: UAE Tender Watch (UTW) v1

## 1. Purpose

This document defines the lean v1 technical architecture for UAE Tender Watch.

The goal is simple:

- monitor exactly 2 UAE public tender portals
- extract visible listing-page metadata
- persist new tenders safely
- match them against user keywords
- send one daily email brief per user
- notify the founder when crawling fails

This is a small production-aware system for a solo founder. It is not designed as a distributed platform.

---

## 2. Core Components

UTW v1 has 6 components only:

1. **Web Frontend**
   - user signup/login
   - keyword profile management
   - simple tenders list page
   - no direct crawler access

2. **Backend API**
   - authentication
   - user/profile CRUD
   - tenders list reads
   - operator status page
   - shared ingestion/data layer used by crawler jobs

3. **Crawler Worker**
   - runs browser automation with `browser-use`
   - visits the 2 configured portals
   - extracts listing-page fields
   - sends structured records into the shared ingestion layer

4. **Scheduler**
   - triggers daily crawl jobs
   - triggers daily email job
   - triggers founder failure alert flow when required

5. **Postgres Database**
   - source of truth for users, tenders, matches, crawl state, and email state

6. **Email Service**
   - sends daily user brief
   - sends founder failure alerts

---

## 3. Design Principles

The architecture follows these rules:

- **deterministic extraction first**
- **AI is optional and secondary**
- **one clean write path for tenders**
- **idempotent persistence**
- **minimal moving parts**
- **crawler isolation from user-facing app**
- **failure in one part must not corrupt another**

---

## 4. High-Level Data Flow

### A. User flow
1. User signs up in the web frontend.
2. User creates or updates a keyword profile.
3. Backend API stores this in Postgres.
4. User later receives daily email alerts and can view tenders in the app.

### B. Crawl flow
1. Scheduler starts crawl job for Source A or Source B.
2. Crawler Worker launches browser automation using `browser-use`.
3. Worker extracts visible listing-page metadata.
4. Worker passes normalized records to the shared ingestion layer.
5. Shared ingestion layer validates, deduplicates, and writes new tenders to Postgres.
6. Optional AI enrichment runs only after core metadata has already been stored successfully.

### C. Matching and alert flow
1. Daily matching job finds recent tenders.
2. Matching logic compares recent tenders against user keyword profiles.
3. New `(user_id, tender_id)` matches are stored.
4. Daily email job gathers unsent matches for each user.
5. Email service sends one daily brief per user.
6. Successful delivery updates delivery state so the same tender is not sent again.

---

## 5. Component Boundaries

## Web Frontend
Responsible for:
- account flows
- keyword profile forms
- tenders list UI
- operator status UI

Not responsible for:
- crawling
- extraction logic
- matching logic
- email dispatch logic

## Backend API
Responsible for:
- user-facing read/write endpoints
- operator-facing status endpoints
- shared ingestion/data layer
- core business rules around data validation and persistence

Not responsible for:
- running browser sessions
- long-running crawl execution

## Crawler Worker
Responsible for:
- portal navigation
- deterministic extraction from listing pages
- normalizing extracted values
- calling the ingestion layer
- optionally calling AI summarization after successful extraction

Not responsible for:
- user authentication
- rendering frontend pages
- making direct business decisions about user-facing alert state outside its run scope

## Scheduler
Responsible for:
- starting crawl runs on schedule
- starting daily email generation on schedule

Not responsible for:
- extraction logic
- persistence logic
- email rendering logic

## Email Service
Responsible for:
- daily brief delivery
- founder failure alerts

Not responsible for:
- tender extraction
- matching decisions
- modifying tender records

---

## 6. Shared Ingestion Layer

The crawler must not write raw records directly into database tables in an ad hoc way.

Instead, crawler output must pass through a **shared ingestion/data layer** that is part of the application codebase.

This layer is responsible for:

- field validation
- normalization
- deduplication
- safe inserts/updates
- assigning source metadata
- recording crawl run results

This keeps crawl logic separate from persistence rules and makes the system easier to test and maintain.

**Write path:**

`Crawler Worker -> Shared Ingestion Layer -> Postgres`

This is the only write path for tender ingestion in v1.

---

## 7. Failure Boundaries

## Crawl failure
If one source crawl fails:

- existing tender data stays available
- the web frontend still works
- the other source can still be crawled
- founder receives failure alert
- failed source can be retried later

## AI enrichment failure
If AI summary generation fails:

- tender record still exists
- title/entity/deadline remain usable
- summary is left empty or null
- matching and email flow continue

## Email failure
If daily email sending fails:

- tender data remains unchanged
- match data remains unchanged
- retry can happen later
- duplicate alerts must still be prevented by delivery state

## Frontend/API failure
If the frontend or API is temporarily unavailable:

- scheduled crawler runs should still be able to execute if the worker and database are healthy
- existing database records are not lost

## Database failure
If Postgres is unavailable:

- crawler ingestion stops
- matching stops
- email generation stops
- no fallback persistence exists in v1
- recovery depends on database restoration

---

## 8. Minimal Observability

Observability in v1 should stay simple.

Required:

### Structured logs
All API and worker logs should be structured and include:
- timestamp
- component
- source name
- run identifier
- status
- error message when applicable

### Last successful run per source
The operator page must show:
- source name
- current source status
- last successful run timestamp
- last failed run timestamp
- short failure reason if latest run failed

### Founder failure alert
The founder must receive an email when:
- a crawl fails
- ingestion fails for a source
- repeated source failures push a source into degraded/broken state

Not required in v1:
- distributed tracing
- custom metrics dashboards
- complex APM tooling

---

## 9. Source Status Model

Each monitored source should expose a simple operational state:

- **healthy**: recent run succeeded
- **degraded**: recent failures occurred but source is still being retried
- **broken**: repeated failures or source became inaccessible/login-walled

This status is operational only. It helps the founder decide whether to fix, retry, or temporarily disable a source.

---

## 10. Code Organization

All UTW-specific implementation should live outside the core `browser_use/` library.

Recommended project shape:

```text
src/
  api/
  frontend/
  crawler/
    portals/
    runner/
  ingestion/
  matching/
  email/
  scheduler/
  db/
  shared/