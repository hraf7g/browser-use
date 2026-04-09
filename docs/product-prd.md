# Product PRD: UAE Tender Watch (UTW)

## 1. Product Description
UAE Tender Watch (UTW) is a minimalist monitoring service that tracks specific public procurement listings from two major UAE portals. It uses deterministic browser automation to script-scrape publicly visible tender listings, extracts core metadata (Title, Issuing Entity, Closing Date), and provides simple email-based notifications. The service aims to reduce the manual overhead of daily portal-checking for a handful of sources, without claiming exhaustive coverage of the UAE's entire procurement market.

## 2. Target User
Solo practitioners, specialized consultants, or small service businesses in the UAE who need frequent updates from two specific, high-volume government portals and currently perform this check manually every 24–48 hours.

## 3. Core Pain Point
Checking multiple government portals is repetitive and prone to human oversight. Even with only two sources, manual checking every day is tedious and risks missing an RFP that has a short closing window.

## 4. Value Proposition
"Automated daily monitoring of your two most important UAE tender sources." UTW creates a reliable notification loop for public opportunities, moving from "pulling" data manually to "pushing" a daily summary to your inbox.

## 5. Main User Outcome
The user receives a daily email alert containing new tender titles and deadlines from the monitored portals, with a link to a simple list page for historical reference.

## 6. Product Constraints & Assumptions (Skeptical View)
- **Crawlability**: Assumption that target portals remain publicly accessible without login walls or aggressive bot blocking.
- **Selector Stability**: Assumption that portal UI changes are infrequent enough to manage as a solo founder.
- **Portals**: Restricted to exactly 2 sources in the MVP.
- **Data Quality**: We only extract what is explicitly visible on the public listing page.
- **No Bid Submission**: Restricted to discovery only.
- **AI Use**: AI is strictly for secondary tasks (summarization/relevance explanation) and is not a dependency for core data extraction.
