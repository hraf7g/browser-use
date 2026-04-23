from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import unquote, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.saudi_misa_config import SAUDI_MISA_CONFIG

_WHITESPACE_RE = re.compile(r"\s+")
_SUPPORT_ID_RE = re.compile(
    r"(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)",
    re.IGNORECASE,
)


class SaudiMisaCrawlerError(RuntimeError):
    """Base class for Saudi MISA crawler failures."""


class SaudiMisaNavigationError(SaudiMisaCrawlerError):
    """Raised when the listing page cannot be loaded or verified."""


class SaudiMisaBlockedError(SaudiMisaCrawlerError):
    """Raised when the public page is blocked by anti-bot or access controls."""


class SaudiMisaExtractionError(SaudiMisaCrawlerError):
    """Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class SaudiMisaRawItem:
    """
    Raw deterministic row extracted from the official Saudi MISA procurements table.

    Notes:
        - This is intentionally source-specific and unnormalized.
        - It preserves the visible competitions-table fields exactly as rendered.
        - The status column exposes a visible Etimad visitor detail link, so the
          href itself is part of the deterministic raw shape.
    """

    item_index: int
    extracted_at: datetime
    page_url: str
    title_text: str
    detail_url: str
    raw_text: str
    visible_reference_number: str | None
    visible_offering_date: str | None
    visible_inquiry_deadline: str | None
    visible_bid_deadline: str | None
    visible_status_link_text: str | None


@dataclass(frozen=True)
class SaudiMisaCrawlResult:
    """Structured result for one Saudi MISA procurements listing-page crawl."""

    source_name: str
    listing_url: str
    final_url: str
    page_title: str
    extracted_at: datetime
    total_items: int
    items: tuple[SaudiMisaRawItem, ...]


class SaudiMisaCrawler:
    """
    Deterministic crawler for the official Saudi MISA procurements page.

    Scope:
        - navigate to the official public procurements page
        - verify the page is the expected source and not an access-control wall
        - extract raw rows from the strongest official competitions table
        - preserve the visible row shape without guessing normalization
    """

    USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self) -> None:
        self._config = SAUDI_MISA_CONFIG

    async def crawl(self) -> SaudiMisaCrawlResult:
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

                    return SaudiMisaCrawlResult(
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
            locale="ar-SA",
            timezone_id="Asia/Riyadh",
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
            raise SaudiMisaNavigationError(
                f"failed to navigate to '{self._config.listing_url}': "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if response is None:
            raise SaudiMisaNavigationError("navigation returned no HTTP response")

        if response.status >= 400:
            raise SaudiMisaNavigationError(
                f"navigation failed with HTTP status {response.status}"
            )

        await self._sleep_with_jitter()

    async def _get_body_text(self, page: Page) -> str:
        """Extract full body text for verification and blocker detection."""
        body_locator = page.locator(self._config.page_body)
        if await body_locator.count() == 0:
            raise SaudiMisaNavigationError("page body selector was not found")
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

        raise SaudiMisaBlockedError(
            "anti-bot or access-control page detected"
            f"{support_suffix}; matched markers={matched_markers}"
        )

    def _verify_page(self, body_text: str) -> None:
        """Verify that expected public page markers are present."""
        normalized_body = body_text.casefold()
        matched_markers = [
            marker
            for marker in self._config.expected_page_text_markers
            if marker.casefold() in normalized_body
        ]
        if not matched_markers:
            raise SaudiMisaNavigationError(
                "page verification failed; expected Saudi MISA procurements markers were not found"
            )

    async def _extract_items(self, page: Page) -> list[SaudiMisaRawItem]:
        """Extract raw competition rows from the structured table."""
        table_locator = page.locator(self._config.structured_table)
        if await table_locator.count() == 0:
            raise SaudiMisaExtractionError("structured procurements table was not found")

        row_locator = page.locator(self._config.structured_rows)
        row_count = await row_locator.count()
        if row_count == 0:
            raise SaudiMisaExtractionError("structured competitions table has zero rows")

        extracted_at = datetime.now(UTC)
        items: list[SaudiMisaRawItem] = []
        seen_urls: set[str] = set()

        for row_index in range(row_count):
            row = row_locator.nth(row_index)
            cells = row.locator("td")
            cell_count = await cells.count()
            if cell_count < 6:
                continue

            values = [
                self._normalize_whitespace(await cells.nth(cell_index).inner_text())
                for cell_index in range(cell_count)
            ]

            title_text = values[0]
            if not title_text:
                continue

            status_link = cells.nth(5).locator("a.wpdt-link-content").first
            href = await status_link.get_attribute("href")
            detail_url = self._normalize_detail_url(href)
            if detail_url is None or detail_url in seen_urls:
                continue

            status_link_text = self._normalize_whitespace(await status_link.inner_text())
            raw_text = self._normalize_whitespace(await row.inner_text())
            if not raw_text:
                continue

            items.append(
                SaudiMisaRawItem(
                    item_index=len(items),
                    extracted_at=extracted_at,
                    page_url=page.url,
                    title_text=title_text,
                    detail_url=detail_url,
                    raw_text=raw_text,
                    visible_reference_number=self._none_if_empty(values[1]),
                    visible_offering_date=self._none_if_empty(values[2]),
                    visible_inquiry_deadline=self._none_if_empty(values[3]),
                    visible_bid_deadline=self._none_if_empty(values[4]),
                    visible_status_link_text=self._none_if_empty(status_link_text),
                )
            )
            seen_urls.add(detail_url)

        if not items:
            raise SaudiMisaExtractionError("no valid competition rows were extracted")

        return items

    def _normalize_detail_url(self, href: str | None) -> str | None:
        """Clean and validate the visible Etimad visitor detail URL."""
        cleaned = self._none_if_empty(href)
        if cleaned is None:
            return None

        if cleaned.startswith("http://#"):
            cleaned = cleaned.removeprefix("http://#")

        cleaned = unquote(cleaned).strip()
        parsed = urlparse(cleaned)
        if parsed.scheme != "https":
            return None
        if parsed.netloc.casefold() != "tenders.etimad.sa":
            return None
        if not parsed.path.startswith("/Tender/DetailsForVisitor"):
            return None
        if "STenderId=" not in parsed.query:
            return None
        return cleaned

    async def _sleep_with_jitter(self) -> None:
        """Wait a bounded randomized interval after navigation."""
        await asyncio.sleep(
            random.uniform(
                self._config.min_jitter_ms / 1000,
                self._config.max_jitter_ms / 1000,
            )
        )

    @staticmethod
    def _normalize_whitespace(value: str) -> str:
        """Collapse whitespace while preserving visible content order."""
        return _WHITESPACE_RE.sub(" ", value.replace("\xa0", " ")).strip()

    @staticmethod
    def _none_if_empty(value: str | None) -> str | None:
        """Convert blank strings to None."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


async def run_saudi_misa_crawl() -> SaudiMisaCrawlResult:
    """Convenience entrypoint for one Saudi MISA crawl."""
    crawler = SaudiMisaCrawler()
    return await crawler.crawl()
