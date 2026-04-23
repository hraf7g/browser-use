from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.oman_tender_board_config import OMAN_TENDER_BOARD_CONFIG

_WHITESPACE_RE = re.compile(r"\s+")
_SUPPORT_ID_RE = re.compile(
    r"(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)",
    re.IGNORECASE,
)
_ONCLICK_NIT_RE = re.compile(r"getNit\('(?P<tender_no>\d+)'\)")
_DATE_FIELD_RE = re.compile(
    r"Sales\s+EndDate:(?P<sales>[0-9]{2}-[0-9]{2}-[0-9]{4})-Bid\s+Closing\s+Date:(?P<closing>[0-9]{2}-[0-9]{2}-[0-9]{4})",
    re.IGNORECASE,
)


class OmanTenderBoardCrawlerError(RuntimeError):
    """Base class for Oman Tender Board crawler failures."""


class OmanTenderBoardNavigationError(OmanTenderBoardCrawlerError):
    """Raised when the listing page cannot be loaded or verified."""


class OmanTenderBoardBlockedError(OmanTenderBoardCrawlerError):
    """Raised when the public page is blocked by anti-bot or access controls."""


class OmanTenderBoardExtractionError(OmanTenderBoardCrawlerError):
    """Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class OmanTenderBoardRawItem:
    """
    Raw deterministic listing item extracted from the Oman Tender Board public page.

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
    visible_entity: str | None
    visible_procurement_category: str | None
    visible_tender_type: str | None
    visible_sales_end_date: str | None
    visible_bid_closing_date: str | None


@dataclass(frozen=True)
class OmanTenderBoardCrawlResult:
    """Structured result for one Oman Tender Board public listing-page crawl."""

    source_name: str
    listing_url: str
    final_url: str
    page_title: str
    extracted_at: datetime
    total_items: int
    items: tuple[OmanTenderBoardRawItem, ...]


class OmanTenderBoardCrawler:
    """
    Deterministic crawler for the Oman Tender Board public new-tenders view.

    Scope:
        - navigate to the official public new-tenders listing
        - verify the page is the expected source and not an anti-bot wall
        - extract raw tender rows from the visible public table
        - derive row-level public detail URLs from the page's own getNit() handler
        - return only source-specific raw content

    Non-goals:
        - no AI extraction
        - no database writes
        - no normalization or ingestion
        - no detail-page crawling yet
    """

    USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self) -> None:
        self._config = OMAN_TENDER_BOARD_CONFIG

    async def crawl(self) -> OmanTenderBoardCrawlResult:
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

                    return OmanTenderBoardCrawlResult(
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
            locale="en-OM",
            timezone_id="Asia/Muscat",
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
            raise OmanTenderBoardNavigationError(
                f"failed to navigate to '{self._config.listing_url}': "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if response is None:
            raise OmanTenderBoardNavigationError("navigation returned no HTTP response")

        if response.status >= 400:
            raise OmanTenderBoardNavigationError(
                f"navigation failed with HTTP status {response.status}"
            )

        await self._sleep_with_jitter()

    async def _get_body_text(self, page: Page) -> str:
        """Extract full body text for verification and blocker detection."""
        body_locator = page.locator(self._config.page_body)
        if await body_locator.count() == 0:
            raise OmanTenderBoardNavigationError("page body selector was not found")
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

        raise OmanTenderBoardBlockedError(
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
            raise OmanTenderBoardNavigationError(
                "page verification failed; expected Oman Tender Board listing markers were not found"
            )

    async def _extract_items(self, page: Page) -> list[OmanTenderBoardRawItem]:
        """Extract raw tender rows from the public new-tenders table."""
        tables = page.locator(self._config.listing_tables)
        table_count = await tables.count()
        if table_count == 0:
            raise OmanTenderBoardExtractionError("no tables were found on the public listing page")

        extracted_rows = None
        for index in range(table_count):
            table = tables.nth(index)
            table_text = self._normalize_whitespace(await table.inner_text())
            if "رقم المناقصة" not in table_text or "إسم المناقصة" not in table_text:
                continue

            extracted_rows = await table.evaluate(
                """
                (table) => {
                  const rows = Array.from(table.querySelectorAll('tbody tr'));
                  return rows.map((row, rowIndex) => {
                    const onclickNode = row.querySelector("[onclick*='getNit(']");
                    const onclick = onclickNode ? (onclickNode.getAttribute('onclick') || '') : '';
                    const cells = Array.from(row.querySelectorAll('td')).map((cell) => (cell.innerText || '').trim());
                    return {
                      rowIndex,
                      rowText: (row.innerText || '').trim(),
                      onclick,
                      cells,
                    };
                  });
                }
                """
            )
            if extracted_rows:
                break

        if not extracted_rows:
            raise OmanTenderBoardExtractionError(
                "public tender listing table was found, but no row data could be extracted"
            )

        extracted_at = datetime.now(UTC)
        items: list[OmanTenderBoardRawItem] = []
        seen_urls: set[str] = set()

        for row_data in extracted_rows:
            onclick = str(row_data.get("onclick", ""))
            if "getNit(" not in onclick:
                continue

            raw_text = self._normalize_whitespace(str(row_data.get("rowText", "")))
            if not raw_text:
                continue

            detail_url = self._build_detail_url_from_onclick(page.url, onclick)
            if detail_url in seen_urls:
                continue

            cells = row_data.get("cells", [])
            if len(cells) < 7:
                continue

            sales_end_date, bid_closing_date = self._extract_date_fields(
                self._normalize_whitespace(cells[6] if len(cells) > 6 else "")
            )

            items.append(
                OmanTenderBoardRawItem(
                    item_index=len(items),
                    extracted_at=extracted_at,
                    page_url=page.url,
                    title_text=self._normalize_whitespace(cells[2] if len(cells) > 2 else ""),
                    detail_url=detail_url,
                    raw_text=raw_text,
                    visible_tender_number=self._none_if_empty(
                        self._normalize_whitespace(cells[1] if len(cells) > 1 else "")
                    ),
                    visible_entity=self._none_if_empty(
                        self._normalize_whitespace(cells[3] if len(cells) > 3 else "")
                    ),
                    visible_procurement_category=self._none_if_empty(
                        self._normalize_whitespace(cells[4] if len(cells) > 4 else "")
                    ),
                    visible_tender_type=self._none_if_empty(
                        self._normalize_whitespace(cells[5] if len(cells) > 5 else "")
                    ),
                    visible_sales_end_date=sales_end_date,
                    visible_bid_closing_date=bid_closing_date,
                )
            )
            seen_urls.add(detail_url)

        if not items:
            raise OmanTenderBoardExtractionError(
                "public listing rows were found, but no non-empty tender rows could be extracted"
            )

        return items

    def _extract_date_fields(self, raw_date_cell: str) -> tuple[str | None, str | None]:
        """Extract visible sales-end and bid-closing dates from the public row text."""
        match = _DATE_FIELD_RE.search(raw_date_cell)
        if match is None:
            return None, None
        return match.group("sales"), match.group("closing")

    def _build_detail_url_from_onclick(self, page_url: str, onclick: str) -> str:
        """Build the public detail URL from the row's real getNit() handler."""
        match = _ONCLICK_NIT_RE.search(onclick)
        if match is None:
            raise OmanTenderBoardExtractionError(
                "public row does not expose the expected getNit() handler"
            )

        tender_no = match.group("tender_no")
        detail_url = urljoin(
            page_url,
            f"/product/nitParameterView?{urlencode({'mode': 'public', 'tenderNo': tender_no, 'PublicUrl': '1'})}",
        )
        return self._validate_detail_url(detail_url)

    def _validate_detail_url(self, detail_url: str) -> str:
        """Validate that the detail URL stays on the expected public detail route."""
        parsed = urlparse(detail_url)
        if parsed.scheme != "https":
            raise OmanTenderBoardExtractionError("detail URL is not https")
        if parsed.netloc != "etendering.tenderboard.gov.om":
            raise OmanTenderBoardExtractionError(
                "detail URL does not stay on etendering.tenderboard.gov.om"
            )
        if parsed.path != "/product/nitParameterView":
            raise OmanTenderBoardExtractionError(
                "detail URL path is not the expected public tender-detail route"
            )

        query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if query_pairs.get("mode") != "public":
            raise OmanTenderBoardExtractionError("detail URL mode is not public")
        if not query_pairs.get("tenderNo"):
            raise OmanTenderBoardExtractionError(
                "detail URL is missing a non-empty tenderNo query parameter"
            )
        if query_pairs.get("PublicUrl") != "1":
            raise OmanTenderBoardExtractionError(
                "detail URL is missing the expected PublicUrl=1 flag"
            )
        return detail_url

    def _normalize_whitespace(self, value: str) -> str:
        """Collapse repeated whitespace while preserving line boundaries."""
        collapsed_lines = [
            _WHITESPACE_RE.sub(" ", line).strip()
            for line in value.splitlines()
            if line.strip()
        ]
        return "\n".join(collapsed_lines)

    def _none_if_empty(self, value: str | None) -> str | None:
        """Convert blank strings to None."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    async def _sleep_with_jitter(self) -> None:
        """Apply bounded deterministic-friendly jitter between actions."""
        jitter_ms = random.randint(
            self._config.min_jitter_ms,
            self._config.max_jitter_ms,
        )
        await asyncio.sleep(jitter_ms / 1000)


async def run_oman_tender_board_crawl() -> OmanTenderBoardCrawlResult:
    """Convenience entrypoint for programmatic verification."""
    crawler = OmanTenderBoardCrawler()
    return await crawler.crawl()
