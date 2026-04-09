# MVP Scope: UAE Tender Watch (UTW)

## 1. In-Scope Features (v1)
*   **Dual-Source Scraper**: Daily automated scraping of exactly 2 public portals (Dubai eSupply and MOF Federal). Deterministic extraction for Title, Entity, and Closing Date using CSS/Playwright selectors.
*   **AI-Enhanced Metadata (Optional)**: Using AI only for:
    1.  Brief tender summary (3-bullet point format).
    2.  Optional relevance explanation (if the user provides keywords).
*   **Simple Alerts**: Daily email notifications (e.g., SendGrid/Standard SMTP) containing new discoveries from the last 24 hours.
*   **Tenders List Page**: A minimalist dashboard containing:
    *   Unified list of scraped tenders.
    *   Sort by closing date.
    *   Filter by source (Portal A or Portal B).
*   **Minimal Operator Page**: A single-view status page for the founder including:
    *   Last execution timestamp per portal.
    *   Current scraper status (Healthy/Broken).
    *   JSON logs for failures (selector errors/timeouts).

## 2. Out-of-Scope Features
*   **Unified Dashboard**: No complex charts or analytics.
*   **Multi-Platform Notifications**: No SMS/WhatsApp alerts for v1.
*   **Full RFP Extraction**: No scraping of tender documents or technical specifications.
*   **Authenticated Scrapes**: No login-required areas.
*   **Full-Text Search across Portals**: No advanced search outside of simple keyword matching.

## 3. Success Criteria for MVP (Measurable Metrics)
*   **Crawl Success Rate**: >90% of daily scheduled crawls must complete without timeout or fatal error.
*   **Field Extraction Completeness**: >95% of successfully crawled tenders must have a valid Title, Issuing Entity, and Closing Date.
*   **Duplicate Rate**: <1% duplicate records in the database for the same tender reference/ID.
*   **Alert Delivery Success**: >99% of daily emails successfully sent to registered users.
*   **Manual Maintenance Burden**: <3 hours of total manual selector/code fixes per month.

## 4. MVP Assumptions
*   Portals maintain a public-facing listing without requiring 2FA or unique user logins for basic metadata.
*   CSS selectors remain stable for at least 1-2 months.
*   AI summaries are useful but not a core requirement for a "Discovery" product.
