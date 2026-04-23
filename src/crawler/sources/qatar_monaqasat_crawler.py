from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import parse_qsl, urljoin, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.qatar_monaqasat_config import QATAR_MONAQASAT_CONFIG

_WHITESPACE_RE = re.compile(r"\s+")
_SUPPORT_ID_RE = re.compile(r"(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)", re.IGNORECASE)
_REFERENCE_RE = re.compile(r"\b\d{1,6}/\d{4}\b")
_PUBLISH_DATE_RE = re.compile(r"Publish date\s*([0-9]{2}/[0-9]{2}/[0-9]{4})", re.IGNORECASE)
_MINISTRY_RE = re.compile(r"Ministry\s+([^\n]+)", re.IGNORECASE)
_TYPE_RE = re.compile(r"Type\s+([^\n]+)", re.IGNORECASE)


class QatarMonaqasatCrawlerError(RuntimeError):
    """Base class for Qatar Monaqasat crawler failures."""


class QatarMonaqasatNavigationError(QatarMonaqasatCrawlerError):
    """Raised when the listing page cannot be loaded or verified."""


class QatarMonaqasatBlockedError(QatarMonaqasatCrawlerError):
    """Raised when the public page is blocked by anti-bot or access controls."""


class QatarMonaqasatExtractionError(QatarMonaqasatCrawlerError):
    """Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class QatarMonaqasatRawItem:
    """
    Raw deterministic listing item extracted from the Qatar Monaqasat public page.

    Notes:
        - This is intentionally source-specific and unnormalized.
        - It is only for proving deterministic public-source access and raw shape.
    """

    item_index: int
    extracted_at: datetime
    page_url: str
    title_text: str
    detail_url: str
    raw_text: str
    visible_reference: str | None
    visible_publish_date: str | None
    visible_ministry: str | None
    visible_tender_type: str | None


@dataclass(frozen=True)
class QatarMonaqasatCrawlResult:
    """Structured result for one Qatar Monaqasat public listing-page crawl."""

    source_name: str
    listing_url: str
    final_url: str
    page_title: str
    extracted_at: datetime
    total_items: int
    items: tuple[QatarMonaqasatRawItem, ...]


class QatarMonaqasatCrawler:
    """
    Deterministic crawler for the Qatar Monaqasat public tenders listing.

    Scope:
        - navigate to the public listing page
        - verify the page is the expected source and not an anti-bot wall
        - extract raw listing artifacts from visible detail links
        - return only source-specific raw content

    Non-goals:
        - no AI extraction
        - no database writes
        - no normalization or ingestion
        - no pagination or detail-page crawling yet
    """

    USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self) -> None:
        self._config = QATAR_MONAQASAT_CONFIG

    async def crawl(self) -> QatarMonaqasatCrawlResult:
        """Run the public-page crawl and return deterministic raw items."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                context = await self._new_context(browser)
                try:
                    page = await context.new_page()
                    await self._navigate(page)
                    body_text = await self._get_body_text(page)
                    self._ensure_not_blocked(body_text)
                    self._verify_page(body_text)
                    items = await self._extract_items(page)
                    extracted_at = datetime.now(UTC)

                    return QatarMonaqasatCrawlResult(
                        source_name=self._config.source_name,
                        listing_url=self._config.listing_url,
                        final_url=page.url,
                        page_title=(await page.title()).strip(),
                        extracted_at=extracted_at,
                        total_items=len(items),
                        items=tuple(items),
                    )
                finally:
                    await context.close()
            finally:
                await browser.close()

    async def _new_context(self, browser: Browser) -> BrowserContext:
        """Create a hardened browser context for deterministic crawling."""
        return await browser.new_context(
            user_agent=self.USER_AGENT,
            viewport={"width": 1440, "height": 1200},
            java_script_enabled=True,
            locale="en-QA",
            timezone_id="Asia/Qatar",
        )

    async def _navigate(self, page: Page) -> None:
        """Navigate to the listing page and allow it to settle."""
        try:
            response = await page.goto(
                self._config.listing_url,
                wait_until="domcontentloaded",
                timeout=self._config.page_load_timeout_ms,
            )
        except Exception as exc:
            raise QatarMonaqasatNavigationError(
                f"failed to navigate to '{self._config.listing_url}': "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if response is None:
            raise QatarMonaqasatNavigationError("navigation returned no HTTP response")

        if response.status >= 400:
            raise QatarMonaqasatNavigationError(
                f"navigation failed with HTTP status {response.status}"
            )

        await self._sleep_with_jitter()

    async def _get_body_text(self, page: Page) -> str:
        """Extract full body text for verification and blocker detection."""
        body_locator = page.locator(self._config.page_body)
        if await body_locator.count() == 0:
            raise QatarMonaqasatNavigationError("page body selector was not found")
        return await body_locator.inner_text()

    def _ensure_not_blocked(self, body_text: str) -> None:
        """Raise an explicit error if the page appears blocked or challenged."""
        normalized_body = body_text.casefold()
        matched_markers = [
            marker
            for marker in self._config.anti_bot_text_markers
            if marker in normalized_body
        ]
        if not matched_markers:
            return

        support_match = _SUPPORT_ID_RE.search(body_text)
        support_suffix = ""
        if support_match:
            support_suffix = f" ({support_match.group(1)}={support_match.group(2)})"

        raise QatarMonaqasatBlockedError(
            "anti-bot or access-control page detected"
            f"{support_suffix}; matched markers={matched_markers}"
        )

    def _verify_page(self, body_text: str) -> None:
        """Verify that expected public listing markers are present."""
        normalized_body = body_text.casefold()
        matched_markers = [
            marker
            for marker in self._config.expected_page_text_markers
            if marker.casefold() in normalized_body
        ]
        if not matched_markers:
            raise QatarMonaqasatNavigationError(
                "page verification failed; expected Qatar Monaqasat listing markers were not found"
            )

    async def _extract_items(self, page: Page) -> list[QatarMonaqasatRawItem]:
        """Extract raw item containers from visible detail links."""
        link_locator = page.locator(self._config.detail_links)
        link_count = await link_locator.count()

        if link_count == 0:
            raise QatarMonaqasatExtractionError("no detail links were found for extraction")

        extracted_at = datetime.now(UTC)
        items: list[QatarMonaqasatRawItem] = []
        seen_urls: set[str] = set()

        for item_index in range(link_count):
            link = link_locator.nth(item_index)
            anchor_text = self._normalize_whitespace(await link.inner_text())
            if not anchor_text or anchor_text.casefold() in self._config.generic_link_labels:
                continue

            href = await link.get_attribute("href")
            if not isinstance(href, str) or not href.strip():
                continue

            detail_url = self._validate_detail_url(urljoin(page.url, href.strip()))
            if detail_url in seen_urls:
                continue

            raw_text = self._normalize_whitespace(await self._extract_link_container_text(link))
            if not raw_text:
                continue

            items.append(
                QatarMonaqasatRawItem(
                    item_index=len(items),
                    extracted_at=extracted_at,
                    page_url=page.url,
                    title_text=anchor_text,
                    detail_url=detail_url,
                    raw_text=raw_text,
                    visible_reference=self._extract_reference(raw_text),
                    visible_publish_date=self._extract_publish_date(raw_text),
                    visible_ministry=self._extract_labeled_value(_MINISTRY_RE, raw_text),
                    visible_tender_type=self._extract_labeled_value(_TYPE_RE, raw_text),
                )
            )
            seen_urls.add(detail_url)

        if not items:
            raise QatarMonaqasatExtractionError(
                "detail links were found, but no non-empty raw item content could be extracted"
            )

        return items

    async def _extract_link_container_text(self, link_locator) -> str:
        """Extract the closest useful ancestor text for a listing artifact."""
        text = await link_locator.evaluate(
            """
            (element) => {
              const minLength = 80;
              let current = element;
              for (let depth = 0; depth < 6 && current; depth += 1) {
                const text = (current.innerText || "").trim();
                if (text.length >= minLength) {
                  return text;
                }
                current = current.parentElement;
              }
              return (element.innerText || "").trim();
            }
            """
        )
        return text if isinstance(text, str) else ""

    def _extract_reference(self, raw_text: str) -> str | None:
        """Extract a visible tender reference when explicitly shown."""
        match = _REFERENCE_RE.search(raw_text)
        if match is None:
            return None
        return match.group(0)

    def _extract_publish_date(self, raw_text: str) -> str | None:
        """Extract a visible publish date when explicitly shown."""
        match = _PUBLISH_DATE_RE.search(raw_text)
        if match is None:
            return None
        return match.group(1)

    def _extract_labeled_value(self, pattern: re.Pattern[str], raw_text: str) -> str | None:
        """Extract a visible labeled field using a deterministic pattern."""
        match = pattern.search(raw_text)
        if match is None:
            return None
        return self._normalize_whitespace(match.group(1))

    def _normalize_whitespace(self, value: str) -> str:
        """Collapse repeated whitespace while preserving line boundaries."""
        collapsed_lines = [
            _WHITESPACE_RE.sub(" ", line).strip()
            for line in value.splitlines()
            if line.strip()
        ]
        return "\n".join(collapsed_lines)

    def _validate_detail_url(self, detail_url: str) -> str:
        """Validate that the detail URL stays on the expected public detail route."""
        parsed = urlparse(detail_url)
        if parsed.scheme != "https":
            raise QatarMonaqasatExtractionError("detail URL is not https")
        if parsed.netloc != "monaqasat.mof.gov.qa":
            raise QatarMonaqasatExtractionError(
                "detail URL does not stay on monaqasat.mof.gov.qa"
            )
        if "/TendersOnlineServices/TenderDetails/" not in parsed.path:
            raise QatarMonaqasatExtractionError(
                "detail URL path is not the expected public tender-detail route"
            )

        path_tail = parsed.path.rstrip("/").split("/")[-1]
        if not path_tail.isdigit():
            query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
            if not query_pairs:
                raise QatarMonaqasatExtractionError(
                    "detail URL has neither numeric path id nor query parameters"
                )

        return detail_url

    async def _sleep_with_jitter(self) -> None:
        """Apply bounded deterministic-friendly jitter between actions."""
        jitter_ms = random.randint(
            self._config.min_jitter_ms,
            self._config.max_jitter_ms,
        )
        await asyncio.sleep(jitter_ms / 1000)


async def run_qatar_monaqasat_crawl() -> QatarMonaqasatCrawlResult:
    """Convenience entrypoint for programmatic verification."""
    crawler = QatarMonaqasatCrawler()
    return await crawler.crawl()
