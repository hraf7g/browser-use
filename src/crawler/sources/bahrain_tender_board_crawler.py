from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.bahrain_tender_board_config import (
    BAHRAIN_TENDER_BOARD_CONFIG,
)

_WHITESPACE_RE = re.compile(r"\s+")
_SUPPORT_ID_RE = re.compile(
    r"(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)",
    re.IGNORECASE,
)
_REFERENCE_RE = re.compile(r"\b\d{1,6}/\d{4}/[A-Z]{2,8}\b")
_PA_REFERENCE_RE = re.compile(r"\(([^()\n]+)\)")
_ONCLICK_NIT_RE = re.compile(r"getNit\('(?P<tender_no>\d+)'\)")


class BahrainTenderBoardCrawlerError(RuntimeError):
    """Base class for Bahrain Tender Board crawler failures."""


class BahrainTenderBoardNavigationError(BahrainTenderBoardCrawlerError):
    """Raised when the listing page cannot be loaded or verified."""


class BahrainTenderBoardBlockedError(BahrainTenderBoardCrawlerError):
    """Raised when the public page is blocked by anti-bot or access controls."""


class BahrainTenderBoardExtractionError(BahrainTenderBoardCrawlerError):
    """Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class BahrainTenderBoardRawItem:
    """
    Raw deterministic listing item extracted from the Bahrain Tender Board public dashboard.

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
    visible_tender_number: str | None
    visible_pa_reference: str | None
    visible_entity: str | None
    visible_time_left: str | None


@dataclass(frozen=True)
class BahrainTenderBoardCrawlResult:
    """Structured result for one Bahrain Tender Board public listing-page crawl."""

    source_name: str
    listing_url: str
    final_url: str
    page_title: str
    extracted_at: datetime
    total_items: int
    items: tuple[BahrainTenderBoardRawItem, ...]


class BahrainTenderBoardCrawler:
    """
    Deterministic crawler for the Bahrain Tender Board public dashboard.

    Scope:
        - navigate to the official public dashboard
        - verify the page is the expected source and not an anti-bot wall
        - extract raw published-tender rows from the public table
        - derive row-level public detail URLs from the page's own getNit() handler
        - return only source-specific raw content

    Non-goals:
        - no AI extraction
        - no database writes
        - no normalization or ingestion
        - no deep detail-page crawling yet
    """

    USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self) -> None:
        self._config = BAHRAIN_TENDER_BOARD_CONFIG

    async def crawl(self) -> BahrainTenderBoardCrawlResult:
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

                    return BahrainTenderBoardCrawlResult(
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
            locale="en-BH",
            timezone_id="Asia/Bahrain",
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
            raise BahrainTenderBoardNavigationError(
                f"failed to navigate to '{self._config.listing_url}': "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if response is None:
            raise BahrainTenderBoardNavigationError("navigation returned no HTTP response")

        if response.status >= 400:
            raise BahrainTenderBoardNavigationError(
                f"navigation failed with HTTP status {response.status}"
            )

        await self._sleep_with_jitter()

    async def _get_body_text(self, page: Page) -> str:
        """Extract full body text for verification and blocker detection."""
        body_locator = page.locator(self._config.page_body)
        if await body_locator.count() == 0:
            raise BahrainTenderBoardNavigationError("page body selector was not found")
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

        raise BahrainTenderBoardBlockedError(
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
            raise BahrainTenderBoardNavigationError(
                "page verification failed; expected Bahrain Tender Board dashboard markers were not found"
            )

    async def _extract_items(self, page: Page) -> list[BahrainTenderBoardRawItem]:
        """Extract raw published-tender rows from the public dashboard table."""
        tables = page.locator(self._config.listing_tables)
        table_count = await tables.count()
        if table_count == 0:
            raise BahrainTenderBoardExtractionError("no tables were found on the public dashboard")

        extracted_rows = None
        for index in range(table_count):
            table = tables.nth(index)
            table_text = self._normalize_whitespace(await table.inner_text())
            if "Tender (PA Ref.) No." not in table_text or "Purchasing Authority" not in table_text:
                continue

            extracted_rows = await table.evaluate(
                """
                (table) => {
                  const rows = Array.from(table.querySelectorAll('tbody tr'));
                  return rows.map((row, rowIndex) => {
                    const cells = Array.from(row.querySelectorAll('td')).map((cell) => (cell.innerText || '').trim());
                    const nitTrigger = row.querySelector("span[onclick*='getNit(']");
                    const onclick = nitTrigger ? (nitTrigger.getAttribute('onclick') || '') : '';
                    return {
                      rowIndex,
                      rowText: (row.innerText || '').trim(),
                      cells,
                      onclick,
                    };
                  });
                }
                """
            )
            if extracted_rows:
                break

        if not extracted_rows:
            raise BahrainTenderBoardExtractionError(
                "published dashboard table was found, but no row data could be extracted"
            )

        extracted_at = datetime.now(UTC)
        items: list[BahrainTenderBoardRawItem] = []
        seen_urls: set[str] = set()

        for row_data in extracted_rows:
            raw_text = self._normalize_whitespace(str(row_data.get("rowText", "")))
            if not raw_text:
                continue

            onclick = str(row_data.get("onclick", ""))
            detail_url = self._build_detail_url_from_onclick(page.url, onclick)
            if detail_url in seen_urls:
                continue

            cells = row_data.get("cells", [])
            primary_cell = self._normalize_whitespace(cells[0] if len(cells) > 0 else "")
            entity = self._normalize_whitespace(cells[1] if len(cells) > 1 else "")
            time_left = self._normalize_whitespace(cells[2] if len(cells) > 2 else "")

            items.append(
                BahrainTenderBoardRawItem(
                    item_index=len(items),
                    extracted_at=extracted_at,
                    page_url=page.url,
                    title_text=self._extract_title(primary_cell),
                    detail_url=detail_url,
                    raw_text=raw_text,
                    visible_tender_number=self._extract_tender_number(primary_cell),
                    visible_pa_reference=self._extract_pa_reference(primary_cell),
                    visible_entity=entity or None,
                    visible_time_left=time_left or None,
                )
            )
            seen_urls.add(detail_url)

        if not items:
            raise BahrainTenderBoardExtractionError(
                "published rows were found, but no non-empty row content could be extracted"
            )

        return items

    def _extract_tender_number(self, raw_text: str) -> str | None:
        """Extract a visible Bahrain tender number when explicitly shown."""
        match = _REFERENCE_RE.search(raw_text)
        if match is None:
            return None
        return match.group(0)

    def _extract_pa_reference(self, raw_text: str) -> str | None:
        """Extract a visible purchasing-authority reference when explicitly shown."""
        first_line = raw_text.splitlines()[0] if raw_text.splitlines() else raw_text
        match = _PA_REFERENCE_RE.search(first_line)
        if match is None:
            return None
        return match.group(1)

    def _extract_title(self, primary_cell: str) -> str:
        """Extract the visible tender subject text from the row primary cell."""
        lines = [line for line in primary_cell.splitlines() if line]
        if len(lines) >= 2:
            normalized = lines[1].strip("() ").strip()
            if normalized:
                return normalized

        for line in lines:
            if _REFERENCE_RE.search(line):
                continue
            normalized = line.strip("() ").strip()
            if normalized:
                return normalized
        raise BahrainTenderBoardExtractionError(
            "unable to derive a stable title from dashboard row text"
        )

    def _build_detail_url_from_onclick(self, page_url: str, onclick: str) -> str:
        """Build the public detail URL from the row's real getNit() handler."""
        match = _ONCLICK_NIT_RE.search(onclick)
        if match is None:
            raise BahrainTenderBoardExtractionError(
                "published row does not expose the expected getNit() handler"
            )

        tender_no = match.group("tender_no")
        detail_url = urljoin(
            page_url,
            f"/Tenders/nitParameterView?{urlencode({'mode': 'public', 'tenderNo': tender_no, 'PublicUrl': '1'})}",
        )
        return self._validate_detail_url(detail_url)

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
            raise BahrainTenderBoardExtractionError("detail URL is not https")
        if parsed.netloc != "etendering.tenderboard.gov.bh":
            raise BahrainTenderBoardExtractionError(
                "detail URL does not stay on etendering.tenderboard.gov.bh"
            )
        if parsed.path != "/Tenders/nitParameterView":
            raise BahrainTenderBoardExtractionError(
                "detail URL path is not the expected public tender-detail route"
            )

        query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if query_pairs.get("mode") != "public":
            raise BahrainTenderBoardExtractionError("detail URL mode is not public")
        if not query_pairs.get("tenderNo"):
            raise BahrainTenderBoardExtractionError(
                "detail URL is missing a non-empty tenderNo query parameter"
            )
        if query_pairs.get("PublicUrl") != "1":
            raise BahrainTenderBoardExtractionError(
                "detail URL is missing the expected PublicUrl=1 flag"
            )
        return detail_url

    async def _sleep_with_jitter(self) -> None:
        """Apply bounded deterministic-friendly jitter between actions."""
        jitter_ms = random.randint(
            self._config.min_jitter_ms,
            self._config.max_jitter_ms,
        )
        await asyncio.sleep(jitter_ms / 1000)


async def run_bahrain_tender_board_crawl() -> BahrainTenderBoardCrawlResult:
    """Convenience entrypoint for programmatic verification."""
    crawler = BahrainTenderBoardCrawler()
    return await crawler.crawl()
