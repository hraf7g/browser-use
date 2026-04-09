# User Flow: UAE Tender Watch (UTW)

## 1. Sign-up & Onboarding
1.  **Welcome**: User visits the landing page.
2.  **Basic Profile**: User creates an account (Email/Password).
3.  **Keyword Setup**: User enters their "Interest Profiles" (e.g., "Cleaning", "IT", "Consultancy").
4.  **Confirm Frequency**: User confirms daily morning email receipt (Standard: 9:00 AM GST).

## 2. Admin / Minimal Operator Flow (Founder Only)
1.  **Scheduled Script**: The `browser-use` automation script runs at a scheduled interval (e.g., nightly).
2.  **Portal Crawling**:
    *   **Portal A (eSupply)**: Script visits the public tenders page and extracts new entries via CSS selectors.
    *   **Portal B (MOF)**: Script repeats for the federal MOF listings.
3.  **Deduplication & Metadata**: 
    *   System **deduplicates** new entries by source URL and/or tender reference number.
    *   **Target (Deterministic)**: Title, Entity, Deadline.
    *   **AI (Optional)**: Short summary based on keyword match.
4.  **Minimal Operator Page (Status Check)**: Founder checks this page to see:
    *   **Last Run Success/Failure** (e.g., "Portal A Scraped Successfully at 3:00 AM").
    *   **Field Coverage Stats** (e.g., "10/10 tenders correctly extracted").
    *   **Error Logs** (e.g., "CSS Selector `table.tenders` not found in Portal B").

## 3. Alert & List Flow (Daily Cycle)
1.  **Email Alert Generation**: At the scheduled time, the system generates an email for each user based on keyword matches.
2.  **Alert Delivery**: User receives the email containing:
    *   **Tender Title**
    *   **Issuing Agency**
    *   **Closing Date** (Highlighted)
    *   **Brief AI Summary** (3 bullets)
3.  **View All (Simple List Page)**: User clicks a link in the email to view the full current list of tenders on a **simple tenders list page**.
4.  **Action**: User clicks the "Source Link" for a specific tender to proceed with official registration/bidding on the government's portal.

## 4. Maintenance & Error Recovery
1.  **Automatic Alerts**: System triggers an **automatic failure alert** to the founder if a crawl or extraction fails.
2.  **Immediate Review**: Founder reviews scraper failures the same day to ensure the notification loop is not broken.
3.  **Manual Update**: If a selector has changed, the founder updates the script and triggers a "Backfill" run for the affected portal.
