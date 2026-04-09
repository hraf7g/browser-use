# Crawler Design: UAE Tender Watch (UTW) v1

## 1. Purpose

This document defines how the UAE Tender Watch crawler should behave in v1.

The crawler’s job is narrow:

- visit exactly 2 configured UAE tender portals
- extract visible listing-page metadata only
- normalize records
- pass records into the shared ingestion layer
- optionally enrich records with a short AI summary after successful extraction

The crawler is not a general web agent. It is a controlled browser automation worker for a small number of known sources.

---

## 2. Design Rules

The crawler must follow these rules:

- deterministic extraction first
- visible listing-page fields only
- no login-required access
- no submission or interaction beyond what is needed to view public listings
- AI is optional and secondary
- low-frequency crawling only
- portal-specific logic must stay isolated
- failures must be explicit and observable

---

## 3. Scope of Extraction

In v1, the crawler only targets metadata visible on the public listing page or a clearly public listing-detail page if needed and safely accessible.

Required target fields:

- title
- issuing entity
- closing date

Optional target fields when available:

- tender reference number
- opening date
- category
- public source URL

The crawler must not assume every portal exposes every field.

If a required field cannot be extracted reliably for a source, that source is not ready for production use.

---

## 4. Output Contract

Each successful extracted tender record should be normalized into a structured internal record before persistence.

That internal record should contain:

- source identifier
- source URL
- title
- issuing entity
- closing date
- tender reference number if available
- optional category if available
- optional opening/publication date if available
- optional AI summary if enrichment succeeds

The crawler does not decide final deduplication at the database level.  
It passes normalized records into the shared ingestion layer, which applies validation, dedupe, and persistence rules.

---

## 5. Crawl Workflow

Each source crawl should follow the same high-level sequence:

1. start crawl run
2. open browser session
3. navigate to configured source entry page
4. wait for target listing content to load
5. extract listing rows or cards using deterministic selectors
6. normalize extracted values
7. pass records to ingestion layer
8. optionally run AI summary generation for newly persisted tenders only
9. mark run success or failure
10. close browser session cleanly

This flow should remain consistent across sources even if selectors differ.

---

## 6. Deterministic Extraction First

Deterministic extraction is the primary method in v1.

That means:

- explicit selectors
- explicit waits
- explicit field parsing
- explicit failure if required fields are missing

The crawler should not use AI to infer:

- title
- deadline
- issuing entity

Those fields must come from deterministic extraction only.

AI may be used later to generate:

- a short 3-bullet summary
- a short keyword relevance explanation if explicitly enabled

If deterministic extraction fails, AI must not be used as a rescue path for core fields.

---

## 7. AI Enrichment Rules

AI enrichment is optional.

It should only run when:

- the tender record has already been ingested successfully
- required fields are present
- the source run did not fail
- cost controls allow it

AI enrichment should be skipped when:

- extraction quality is uncertain
- the page structure broke
- the crawler is in recovery mode
- the tender already has an existing summary

If AI fails:

- leave `ai_summary` empty
- do not fail the entire crawl
- do not block matching or daily email generation

---

## 8. Source Inventory for v1

Exactly 2 sources are in scope for the first implementation.

## Source A: Dubai eSupply
- Base URL: `https://esupply.dubai.gov.ae`
- Verification status: **partially verified**
- Why partially verified:
  - the portal URL is known
  - public tender-related entry points appear to exist
  - exact public listing-page behavior still requires manual implementation validation
- Risk level: medium to high
- Primary risks:
  - dynamic rendering
  - selector fragility
  - inconsistent listing structure

## Source B: Federal MOF
- Base URL: `https://mprocurement.mof.gov.ae/`
- Verification status: **unverified**
- Why unverified:
  - base URL is known
  - public listing accessibility and stable extraction path are not yet confirmed
- Risk level: high
- Primary risks:
  - login wall or access restrictions
  - dynamic loading
  - unstable public listing path

These labels must remain conservative until manual implementation confirms actual accessibility and extractability.

---

## 9. Portal-Specific Isolation

Each source must have its own isolated crawler module.

That module should contain only source-specific details such as:

- entry URL
- navigation steps
- selectors
- wait strategy
- row/card parsing logic
- source-specific normalization quirks

Shared concerns must stay outside source modules:

- browser session setup
- ingestion
- deduplication logic
- run lifecycle handling
- logging
- retry handling
- AI enrichment trigger rules

This keeps one broken source from contaminating the logic for the other.

---

## 10. Wait Strategy

The crawler must use explicit waits, not fragile timing guesses.

Preferred approach:

- wait for page load state where useful
- wait for a specific listing container or row/card selector
- fail clearly if target content does not appear within timeout

Avoid:

- long arbitrary sleeps as the primary loading strategy
- aggressive repeated refreshes
- hidden interactions that mimic suspicious behavior

Small randomized jitter between steps is acceptable, but it is not a substitute for correct wait logic.

---

## 11. Timeout Policy

Timeouts must stay practical.

Recommended v1 policy:

- one overall timeout per source run
- one shorter timeout per important page-load step
- fail fast when the expected listing container never appears

The exact timeout values can be finalized in implementation, but the principle is:

- long enough to handle real government site latency
- short enough to avoid hanging workers

Do not let a single bad source block the full daily pipeline for too long.

---

## 12. Retry Policy

Retries should be conservative.

Recommended v1 behavior:

- retry a failed source crawl at most 1 to 2 additional times
- only retry for transient-looking failures such as timeout or temporary navigation failure
- do not loop endlessly on selector failures
- after repeated failures, record the source as degraded or broken and stop retrying until the next scheduled run or manual intervention

This avoids burning time and compute on a broken portal.

---

## 13. Deduplication Expectations

Crawler-side deduplication should be minimal.

The crawler may avoid obvious duplicates seen in the same run, but the source of truth for dedupe is the shared ingestion layer plus database constraints.

Primary dedupe approach:

- use `(source_id, tender_ref)` when a stable tender reference exists
- otherwise use a deterministic fallback `dedupe_key`

The crawler must not assume every source provides a reliable reference number.

---

## 14. Source Degradation Rules

If a source becomes unstable, the crawler must degrade gracefully.

Examples of degradation triggers:

- repeated selector failures
- repeated timeouts
- public listing becomes inaccessible
- listing becomes login-walled
- portal returns no usable listing content for repeated runs

Required behavior:

1. mark source `degraded` after repeated failures
2. escalate to `broken` after threshold is crossed
3. send founder alert
4. reduce or pause repeated failed runs if configured threshold is reached
5. leave existing tender data intact

This is an operational safety rule, not a product feature.

---

## 15. Anti-Bot and Safety Posture

The crawler must operate conservatively.

v1 posture:

- low crawl frequency only
- exactly one scheduled run per source per day unless manual retry is needed
- no bypassing protections
- no fake account creation
- no aggressive scraping behavior
- no rotating proxy strategy in v1 unless a source is later shown to require it and the product decision explicitly allows it

The safest path for v1 is to behave like a slow, careful reader of a small number of public pages.

---

## 16. Failure Handling

A crawl run should fail clearly when:

- the target listing page cannot be reached
- the expected listing structure does not appear
- required fields cannot be extracted
- normalized records are invalid

When that happens:

- record the run as failed
- store a short failure reason
- store the failure step
- send founder alert
- continue processing the other source if applicable

Do not silently swallow extraction failures.

---

## 17. Founder Maintenance Expectations

The founder is expected to handle source breakage manually in v1.

That means:

- review failure alerts the same day
- inspect logs for selector or navigation breakage
- update source-specific crawler logic
- rerun the affected source when appropriate

This is acceptable in v1 because there are only 2 sources.

---

## 18. What the Crawler Must Not Do

The crawler must not:

- log into protected areas
- submit bids
- fill procurement forms
- download private documents behind authentication
- make legal/compliance judgments
- scrape beyond the narrow source scope of v1
- mutate core browser-use library behavior for product-specific shortcuts

---

## 19. Final v1 Crawler Philosophy

UTW v1 does not need a clever crawler.

It needs a crawler that is:

- predictable
- debuggable
- conservative
- source-isolated
- deterministic first
- safe to operate daily

That is the correct quality bar for a production-aware first version.