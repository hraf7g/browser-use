# Implementation Plan: UAE Tender Watch (UTW) v1

## 1. Purpose

This document defines the implementation order for UAE Tender Watch v1.

The build must prove the core product loop before browser automation is introduced:

- user signs up
- user saves keyword profile
- tender enters the system
- tender is matched to the user
- daily email is generated

Crawler work comes later.

---

## 2. Smallest Useful Vertical Slice

The first working vertical slice is:

1. user signup/login
2. keyword profile save
3. manual tender insertion through the shared ingestion path
4. keyword match creation
5. daily email generation using a local/dev email stub

This vertical slice does **not** require any crawler code.

Why this is the right first slice:

- proves the database model
- proves the ingestion path
- proves duplicate protection
- proves matching logic
- proves email generation flow
- avoids early dependency on fragile portal automation

---

## 3. Implementation Order

## Phase 1: Core Foundation

1. **Project scaffolding**
   - create `src/` structure
   - bootstrap API app
   - bootstrap config loading
   - add health endpoint
   - set up local development environment

2. **Database and migrations**
   - implement models from `docs/data-model.md`
   - create migration flow
   - seed the 2 source records
   - verify local DB bootstraps cleanly

3. **Shared ingestion layer**
   - implement tender validation
   - implement normalization
   - implement deduplication
   - implement safe insert behavior
   - make this testable without crawler code

This phase must be stable before any browser automation starts.

---

## 4. Phase 2: User Core

1. **Authentication**
   - signup
   - login
   - token issuance/validation

2. **Keyword profile management**
   - get current profile
   - create/update keyword profile

3. **Minimal tenders read path**
   - tenders list endpoint
   - simple tenders list UI page

This phase makes the app usable with manually inserted tenders.

---

## 5. Phase 3: Vertical Slice Proof

1. **Manual tender insertion path**
   - use the shared ingestion layer with test/manual data
   - do not build crawler yet

2. **Matching logic**
   - match new tenders against keyword profiles
   - create unique `tender_matches`

3. **Local/dev email backend**
   - generate daily brief content
   - send to console/file/local sink instead of SES

This is the first “real product loop” milestone.

---

## 6. Phase 4: Crawl Operations Foundation

1. **Crawl run tracking**
   - source status updates
   - run history
   - failure capture

2. **Operator status API/page**
   - show last successful run
   - show current source status
   - show recent failure reason

This gives the product a place to expose crawler state before live crawler rollout.

---

## 7. Phase 5: First Crawler Integration

1. **Crawler runner foundation**
   - browser-use integration boundary
   - source runner lifecycle
   - deterministic extraction flow
   - worker logging

2. **Source A implementation**
   - build first source-specific crawler
   - validate extraction against fixture/snapshot first
   - then manually validate against live portal
   - persist through ingestion layer only

No AI summarization yet unless deterministic extraction is already stable.

---

## 8. Phase 6: Second Crawler Integration

1. **Source B implementation**
   - same pattern as Source A
   - fixture/snapshot validation first
   - manual live validation second
   - persist through same ingestion layer

2. **Multi-source stabilization**
   - confirm one failed source does not block the other
   - confirm duplicate rules still hold

---

## 9. Phase 7: AI Enrichment and Production Email

1. **Optional AI summarization**
   - only for already-persisted tenders
   - only after deterministic extraction is stable
   - must degrade gracefully on failure

2. **SES integration**
   - replace local/dev email backend
   - keep email generation logic unchanged where possible
   - production delivery only after local email path is already proven

3. **Founder failure alerts**
   - production email alert on crawl/persistence failure

---

## 10. Mandatory Checklists

## Done before crawler work starts

- database schema is migrated and stable
- source records are seeded
- ingestion layer is implemented
- ingestion deduplication is tested
- manual tender insertion works
- keyword matching works against manual data
- tenders list endpoint works
- local/dev email brief generation works
- basic operator status model exists

## Done before SES starts

- daily brief generation is already correct using local/dev stub
- duplicate alert prevention is verified
- `tender_matches.sent_at` behavior is correct
- failure cases for email send are understood
- AWS account and SES sending prerequisites are ready

---

## 11. Testing and Stubbing Policy

## Test first
- ingestion deduplication
- keyword matching
- duplicate alert prevention
- tenders list read path

## Stub early
- tender discovery via manual inserts
- email delivery via local/dev backend
- AI summarization via no-op or fixed placeholder

## Test crawler against fixtures first
- static HTML snapshots
- deterministic selector checks
- parser normalization tests

Only after that should live portal validation happen.

---

## 12. Do Not Build Yet

Do not build these during v1 implementation:

- payment/subscription billing
- multi-factor auth
- social login
- instant notifications
- WhatsApp/SMS delivery
- PDF/document extraction
- team/org features
- proposal drafting
- bid submission
- admin CRUD panels for all tables

---

## 13. Final Implementation Principle

The correct order is:

1. prove the app loop without crawling
2. prove ingestion and matching
3. prove daily email generation
4. then add crawler source 1
5. then add crawler source 2
6. then add optional AI and production email

That order minimizes wasted work and keeps the fragile part of the product until later.