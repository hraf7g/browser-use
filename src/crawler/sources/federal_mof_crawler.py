from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.federal_mof_config import FEDERAL_MOF_CONFIG


class FederalMOFCrawlerError(RuntimeError):
    """Base class for Federal MOF crawler failures."""


class FederalMOFNavigationError(FederalMOFCrawlerError):
    """Raised when the listing page cannot be loaded or verified."""


class FederalMOFExtractionError(FederalMOFCrawlerError):
    """Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class FederalMOFLinkItem:
    """
    Raw deterministic public content link extracted from the Federal MOF page.

    Notes:
        - This is intentionally raw and source-specific.
        - It is for structural verification first, not tender normalization yet.
        - No heuristic field guessing is allowed here.
    """

    item_index: int
    extracted_at: datetime
    page_url: str
    link_text: str
    href: str | None


@dataclass(frozen=True)
class FederalMOFTableRow:
    """
    Raw deterministic table row extracted from the Federal MOF page.

    Notes:
        - This is intentionally raw and source-specific.
        - Mapping into normalized tender ingestion payloads will happen later
          only if the source actually exposes structured row data.
    """

    row_index: int
    extracted_at: datetime
    page_url: str
    cells: tuple[str, ...]
    row_text: str


@dataclass(frozen=True)
class FederalMOFCrawlResult:
    """Structured result for one Federal MOF listing-page crawl."""

    source_name: str
    listing_url: str
    page_title: str
    extracted_at: datetime
    total_links: int
    total_table_rows: int
    links: tuple[FederalMOFLinkItem, ...]
    table_rows: tuple[FederalMOFTableRow, ...]


class FederalMOFCrawler:
    """
    Deterministic crawler for the Federal MOF public opportunities page.

    Scope:
        - navigate to the configured public page
        - wait for the page to stabilize
        - verify expected Arabic/English public text markers exist
        - extract raw public links from main content
        - extract raw table rows if tables are present
        - return raw structured content for later source-shape decisions

    Non-goals:
        - no AI extraction
        - no ingestion/database writes
        - no field guessing from unverified layouts
        - no deep click traversal yet
    """

    USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self) -> None:
        self._config = FEDERAL_MOF_CONFIG

    async def crawl(self) -> FederalMOFCrawlResult:
        """Run the public-page crawl and return deterministic raw content."""
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                context = await self._new_context(browser)
                try:
                    page = await context.new_page()
                    await self._navigate(page)
                    await self._verify_page(page)

                    links = await self._extract_links(page)
                    table_rows = await self._extract_table_rows(page)
                    page_title = await page.title()
                    extracted_at = datetime.now(UTC)

                    return FederalMOFCrawlResult(
                        source_name=self._config.source_name,
                        listing_url=page.url,
                        page_title=page_title.strip(),
                        extracted_at=extracted_at,
                        total_links=len(links),
                        total_table_rows=len(table_rows),
                        links=tuple(links),
                        table_rows=tuple(table_rows),
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
            locale="ar-AE",
            timezone_id="Asia/Dubai",
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
            raise FederalMOFNavigationError(
                f"failed to navigate to '{self._config.listing_url}'"
            ) from exc

        if response is None:
            raise FederalMOFNavigationError("navigation returned no HTTP response")

        if response.status >= 400:
            raise FederalMOFNavigationError(
                f"navigation failed with HTTP status {response.status}"
            )

        await self._sleep_with_jitter()

    async def _verify_page(self, page: Page) -> None:
        """Verify that the page body contains expected Arabic/English markers."""
        body_locator = page.locator(self._config.page_body)
        if await body_locator.count() == 0:
            raise FederalMOFNavigationError("page body selector was not found")

        body_text = await body_locator.inner_text()
        normalized_body = body_text.casefold()

        matched_markers = [
            marker
            for marker in self._config.expected_page_text_markers
            if marker.casefold() in normalized_body
        ]

        if not matched_markers:
            raise FederalMOFNavigationError(
                "page verification failed; expected text markers were not found"
            )

    async def _extract_links(self, page: Page) -> list[FederalMOFLinkItem]:
        """Extract raw public content links from the main content area."""
        link_locator = page.locator(self._config.article_links)
        link_count = await link_locator.count()
        extracted_at = datetime.now(UTC)

        extracted_links: list[FederalMOFLinkItem] = []
        for item_index in range(link_count):
            link = link_locator.nth(item_index)
            link_text = (await link.inner_text()).strip()
            href = await link.get_attribute("href")

            if not link_text:
                continue

            extracted_links.append(
                FederalMOFLinkItem(
                    item_index=item_index,
                    extracted_at=extracted_at,
                    page_url=page.url,
                    link_text=link_text,
                    href=href.strip() if isinstance(href, str) and href.strip() else None,
                )
            )

        return extracted_links

    async def _extract_table_rows(self, page: Page) -> list[FederalMOFTableRow]:
        """Extract raw table row/cell content if public tables are present."""
        row_locator = page.locator(self._config.table_rows)
        row_count = await row_locator.count()

        if row_count == 0:
            return []

        extracted_at = datetime.now(UTC)
        extracted_rows: list[FederalMOFTableRow] = []

        for row_index in range(row_count):
            row = row_locator.nth(row_index)
            row_text = (await row.inner_text()).strip()

            if not row_text:
                continue

            cell_locator = row.locator(self._config.table_cells)
            cell_count = await cell_locator.count()

            if cell_count == 0:
                continue

            cells: list[str] = []
            for cell_index in range(cell_count):
                cell_text = (await cell_locator.nth(cell_index).inner_text()).strip()
                if cell_text:
                    cells.append(cell_text)

            if not cells:
                continue

            extracted_rows.append(
                FederalMOFTableRow(
                    row_index=row_index,
                    extracted_at=extracted_at,
                    page_url=page.url,
                    cells=tuple(cells),
                    row_text=row_text,
                )
            )

        return extracted_rows

    async def _sleep_with_jitter(self) -> None:
        """Apply bounded deterministic-friendly jitter between actions."""
        jitter_ms = random.randint(
            self._config.min_jitter_ms,
            self._config.max_jitter_ms,
        )
        await asyncio.sleep(jitter_ms / 1000)


async def run_federal_mof_crawl() -> FederalMOFCrawlResult:
    """Convenience entrypoint for one Federal MOF crawl."""
    crawler = FederalMOFCrawler()
    return await crawler.crawl()
