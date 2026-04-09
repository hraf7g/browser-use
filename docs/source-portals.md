# Source Portals: UAE Tender Watch (UTW)

## 1. Monitor Portals (Exactly 2 for MVP)

| Portal Name | Public URL | Verification Status | Extract Design | Notes / Risk |
| :--- | :--- | :--- | :--- | :--- |
| **Dubai eSupply** | `https://esupply.dubai.gov.ae` | **Partially Verified** (via search, but not logged in/manually browsed) | Deterministic for: Title, Entity, Opening/Closing Dates. AI for: 3-point summary. | Highest volume portal for Dubai entities. Uses dynamic layout; high risk of selector fragility. |
| **Federal MOF** | `https://mprocurement.mof.gov.ae/` | **Unverified** (URL confirmed; public access to listings not manually tested) | Deterministic for: Tender No, Title, Ministry, End Date. AI for: Optional summary. | Primary federal source. Potential for login-wall if not specifically on the "Public Listings" page. |

## 2. Extraction Strategy (Deterministic vs AI)

### A. Phase 1: Deterministic (Priority)
For each new tender, use CSS Selectors or Playwright to extract:
*   **Unique Reference Number**
*   **Exact Tender Title**
*   **Issuing Entity Name**
*   **Closing Date/Time** (Critical field)

### B. Phase 2: AI Enrichment (Optional)
If deterministic extraction is successful, invoke AI (e.g., `ChatBrowserUse`) to:
*   Generate a **Short Summary** from the tender headline/type.
*   Provide an **Optional Relevance Explanation** based on simple user keywords.
*   **AI Goal**: Enrich the basic metadata, but never be the source of truth for the title or deadline.

## 3. Risk Assessment
*   **Dubai eSupply**: Known to use complex JS. May require `wait_for_selector` or `wait_until_visible` logic.
*   **Federal MOF**: Dynamic portals often have "No data found" errors if JS loads slowly.
*   **Selector Failures**: UI updates are the biggest threat. Daily runs will log selector presence to the operator page for monitoring.
*   **Bot-Detection**: Government sites may use managed rulesets (Cloudflare/Akamai). Strategy is limited to 1 run/day or 2 runs/day with high jitter.

## 4. Manual Maintenance
The founder will manually verify these two portals every 48 hours for the first 2 weeks to ensure selector stability.
