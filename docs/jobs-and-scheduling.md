# Jobs and Scheduling: UAE Tender Watch (UTW) v1

## 1. Purpose

This document defines the scheduled job flow for UAE Tender Watch v1.

The job system must do only what the product needs:

1. crawl Source A
2. crawl Source B
3. persist and deduplicate new tenders
4. optionally enrich with AI summaries
5. match tenders against user keywords
6. send one daily email per user
7. alert the founder when crawl-related failures happen

This is a small daily batch workflow, not a real-time event system.

---

## 2. Design Rules

The job flow must follow these rules:

- keep execution simple
- isolate source failures
- make all writes idempotent
- do not let AI enrichment block core product behavior
- do not let email retries create duplicate user alerts
- keep founder failure alerts explicit and immediate for crawl/persistence failures

---

## 3. Daily Job Sequence

## Step 1: Crawl Source A
The scheduler starts the crawl job for the first configured source.

What it does:
- launches the crawler worker
- navigates the source
- extracts visible listing-page fields
- sends normalized records into the shared ingestion layer

If it fails:
- record failed crawl run
- update source health state
- send founder failure alert
- continue with Source B later in the cycle

## Step 2: Crawl Source B
The scheduler starts the crawl job for the second configured source.

What it does:
- same pattern as Source A
- runs independently of Source A success or failure

If it fails:
- record failed crawl run
- update source health state
- send founder failure alert

---

## 4. Persistence and Deduplication

Persistence happens as part of each crawl run through the shared ingestion layer.

What it does:
- validates required fields
- normalizes values
- applies dedupe rules
- inserts new tenders
- skips already-known tenders safely

Idempotency rule:
- reprocessing the same extracted tender must not create duplicate tender rows

Primary dedupe logic:
- use `(source_id, tender_ref)` when `tender_ref` exists
- otherwise use fallback `dedupe_key`

This means the same source can be crawled again without corrupting the data set.

---

## 5. Optional AI Enrichment

After new tenders have been persisted, optional AI enrichment may run.

What it does:
- finds newly created tenders with no `ai_summary`
- generates a short summary
- saves it if successful

What it must not do:
- block keyword matching
- block daily email generation
- override core metadata
- rerun forever on repeated failures

If AI enrichment fails:
- keep `ai_summary` empty
- continue the rest of the daily pipeline

Idempotency rule:
- a tender that already has `ai_summary` should not be enriched again unless explicitly reprocessed later by maintenance logic

---

## 6. Keyword Matching Job

After the crawl window is complete, the matching job runs.

What it does:
- looks at newly discovered tenders since the previous cycle
- compares them against user keyword profiles
- creates rows in `tender_matches` for valid `(user_id, tender_id)` pairs

What it must not do:
- create duplicate matches
- depend on AI summary presence
- mutate tender data

Idempotency rule:
- the unique constraint on `(user_id, tender_id)` prevents duplicate matches across retries

Matching can use:
- title
- issuing entity if useful
- category if available
- user keywords

v1 should keep this simple and deterministic.

---

## 7. Daily User Email Job

After matching is complete, the daily email job runs.

What it does:
- gathers all unsent matches for each active user
- builds one daily brief per user
- sends the brief
- marks the included matches as sent only after successful delivery

A user should receive:
- at most one daily brief per scheduled cycle
- only tenders not already delivered successfully

Delivery state rule:
- do not mark `sent_at` before successful email delivery
- if delivery fails, matches remain unsent and can be retried later

This prevents silent data loss.

---

## 8. Founder Failure Alert Job

Founder alerts are not part of the normal user brief flow.

They should trigger when:
- a source crawl fails
- ingestion fails for a source
- repeated source failures move a source into degraded or broken state

Founder alerts should contain:
- source name
- failure step
- short failure reason
- run time
- whether the source is now degraded or broken

This alert should be sent as soon as the failure is confirmed, not delayed until the next user email cycle.

---

## 9. Dependency Order

The dependency chain is simple:

1. crawl source A
2. crawl source B
3. persist/dedupe during crawl
4. optional enrichment for newly persisted tenders
5. keyword matching
6. daily user email generation

Important clarifications:

- crawl A does not depend on crawl B
- one failed source must not block processing of the other source
- keyword matching depends on tender persistence, not on AI enrichment
- user email depends on successful matching, not on both sources being healthy

---

## 10. Partial Failure Handling

## Case: one source fails
Expected behavior:
- failed source is recorded
- founder is alerted
- successful source data still flows through matching and email generation

## Case: both sources fail
Expected behavior:
- both failures are recorded
- founder is alerted
- no new tenders are processed that day
- daily user email may send nothing or may be skipped depending on implementation policy, but it must not send broken or misleading content

## Case: enrichment fails
Expected behavior:
- continue without AI summary
- matching still runs
- daily email still runs

## Case: email sending fails
Expected behavior:
- record failure in `email_deliveries`
- do not mark `tender_matches.sent_at`
- allow safe retry later

---

## 11. Duplicate Prevention Rules

There are two duplicate problems to prevent:

## Duplicate tender rows
Prevented by:
- ingestion-layer normalization
- database dedupe constraints

## Duplicate user alerts
Prevented by:
- unique constraint on `(user_id, tender_id)` in `tender_matches`
- marking `sent_at` only after successful email delivery
- querying only unsent matches during email generation

This combination is enough for v1 if implemented correctly.

---

## 12. Retry Rules

Retries should stay conservative.

## Crawl retries
Allowed for:
- transient timeout
- temporary navigation failure

Not useful for:
- obvious selector breakage
- login wall
- structural page change

Recommended behavior:
- limited retry count only
- after repeated failure, mark source degraded or broken

## Email retries
Allowed for:
- transient delivery failure

Not allowed to create:
- duplicate `tender_matches`
- duplicate sent state
- multiple daily briefs for the same unsent set in the same cycle unless the previous send clearly failed

## Enrichment retries
Low priority in v1.
If enrichment fails repeatedly, skip it and continue operating the product.

---

## 13. Schedule Philosophy

The exact clock times can be set in implementation, but the v1 schedule should follow this pattern:

- early daily crawl window
- matching after crawl completion
- user email brief later in the morning
- founder failure alert immediately on failure

The system does not need minute-by-minute execution precision.
It needs a predictable daily cycle.

---

## 14. Synchronous vs Asynchronous Guidance

Keep this practical:

- source crawl jobs may run separately
- matching should run after crawl persistence is done
- email generation should run after matching is done

Do not overcomplicate v1 with advanced orchestration tooling.
Simple scheduled jobs with clear ordering are enough.

---

## 15. Operational Notes

The founder should be able to answer these questions easily:

- did each source crawl today?
- did it succeed or fail?
- how many new tenders were added?
- were user matches created?
- were daily emails sent?
- which source is degraded or broken?

The job system should support those answers directly through database state and logs.

---

## 16. What v1 Scheduling Does Not Include

This job model does **not** include:

- real-time alerts
- queue fan-out across many workers
- streaming updates
- complex DAG orchestration
- per-user custom schedules
- multi-region job routing

Those are intentionally out of scope.

---

## 17. Final v1 Scheduling Philosophy

UTW v1 is a small batch product.

The right job system is:

- simple
- idempotent
- failure-aware
- easy to reason about
- easy to recover manually when needed

That is the correct standard before scaling anything further.