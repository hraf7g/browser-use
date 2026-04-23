from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.saudi_moh_config import SAUDI_MOH_CONFIG

_DATE_TEXT_RE = re.compile(r'^[A-Z][a-z]+ ?\d{1,2}, \d{4}$')
_WHITESPACE_RE = re.compile(r'\s+')
_SUPPORT_ID_RE = re.compile(
    r'(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)',
    re.IGNORECASE,
)


class SaudiMohCrawlerError(RuntimeError):
    """Base class for Saudi MOH crawler failures."""


class SaudiMohNavigationError(SaudiMohCrawlerError):
    """Raised when the listing page cannot be loaded or verified."""


class SaudiMohBlockedError(SaudiMohCrawlerError):
    """Raised when the public page is blocked by anti-bot or access controls."""


class SaudiMohExtractionError(SaudiMohCrawlerError):
    """Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class SaudiMohRawItem:
    """
    Raw deterministic tender row extracted from the official Saudi MOH page.

    Notes:
        - This shape is intentionally source-specific and unnormalized.
        - The current MOH surface is table/text driven rather than a row-link
          listing, so detail_url remains optional and is only populated when a
          row-level public link is visibly present.
        - Visible date fields are preserved exactly as rendered.
    """

    item_index: int
    extracted_at: datetime
    page_url: str
    source_section: str
    title_text: str
    detail_url: str | None
    raw_text: str
    visible_tender_number: str | None
    visible_tendering_date: str | None
    visible_bidding_deadline: str | None
    visible_opening_date: str | None
    visible_status: str | None


@dataclass(frozen=True)
class SaudiMohCrawlResult:
    """Structured result for one Saudi MOH tenders page crawl."""

    source_name: str
    listing_url: str
    final_url: str
    page_title: str
    extracted_at: datetime
    total_items: int
    items: tuple[SaudiMohRawItem, ...]


class SaudiMohCrawler:
    """
    Deterministic crawler for the official Saudi MOH tenders public page.

    Scope:
        - navigate to the official public MOH tenders page
        - verify that the page is the expected public source
        - extract visible structured tender rows from the strongest text tables
        - return only source-specific raw content

    Non-goals:
        - no normalization
        - no DB writes
        - no ingestion or run-service logic
    """

    USER_AGENT: Final[str] = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )

    def __init__(self) -> None:
        self._config = SAUDI_MOH_CONFIG

    async def crawl(self) -> SaudiMohCrawlResult:
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
                    items = self._extract_items(body_text=body_text, page_url=page.url)
                    extracted_at = datetime.now(UTC)

                    return SaudiMohCrawlResult(
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
            viewport={'width': 1440, 'height': 1200},
            java_script_enabled=True,
            locale='en-US',
            timezone_id='Asia/Riyadh',
        )

    async def _navigate(self, page: Page) -> None:
        """Navigate to the listing page and allow it to settle."""
        try:
            response = await page.goto(
                self._config.listing_url,
                wait_until='domcontentloaded',
                timeout=self._config.page_load_timeout_ms,
            )
        except Exception as exc:
            raise SaudiMohNavigationError(
                f"failed to navigate to '{self._config.listing_url}': "
                f'{type(exc).__name__}: {exc}'
            ) from exc

        if response is None:
            raise SaudiMohNavigationError('navigation returned no HTTP response')

        if response.status >= 400:
            raise SaudiMohNavigationError(
                f'navigation failed with HTTP status {response.status}'
            )

        await self._sleep_with_jitter()

    async def _get_body_text(self, page: Page) -> str:
        """Extract full body text for verification and raw parsing."""
        body_locator = page.locator(self._config.page_body)
        if await body_locator.count() == 0:
            raise SaudiMohNavigationError('page body selector was not found')
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
        support_suffix = ''
        if support_match:
            support_suffix = f' ({support_match.group(1)}={support_match.group(2)})'

        raise SaudiMohBlockedError(
            'anti-bot or access-control page detected'
            f'{support_suffix}; matched markers={matched_markers}'
        )

    def _verify_page(self, body_text: str) -> None:
        """Verify that expected public page markers are present."""
        normalized_body = body_text.casefold()
        matched_markers = [
            marker
            for marker in self._config.expected_page_text_markers
            if marker.casefold() in normalized_body
        ]
        if len(matched_markers) < 3:
            raise SaudiMohNavigationError(
                'page verification failed; expected Saudi MOH tender markers were not found'
            )

    def _extract_items(self, *, body_text: str, page_url: str) -> list[SaudiMohRawItem]:
        """Extract visible tender rows from the strongest structured MOH sections."""
        lines = self._to_lines(body_text)
        if not lines:
            raise SaudiMohExtractionError('page body text was empty after normalization')

        extracted_at = datetime.now(UTC)
        items: list[SaudiMohRawItem] = []

        items.extend(
            self._parse_planned_section(
                lines=lines,
                page_url=page_url,
                extracted_at=extracted_at,
            )
        )
        items.extend(
            self._parse_submission_deadline_section(
                lines=lines,
                page_url=page_url,
                extracted_at=extracted_at,
                start_index=len(items),
            )
        )

        if not items:
            raise SaudiMohExtractionError('no valid MOH tender rows were extracted')

        return items

    def _parse_planned_section(
        self,
        *,
        lines: list[str],
        page_url: str,
        extracted_at: datetime,
    ) -> list[SaudiMohRawItem]:
        """Parse the planned tenders table that exposes launch dates clearly."""
        heading = 'Planned Tenders and procurement:'
        boundary = 'Archived Tenders and Procurement (Closed):'
        start = self._find_line_index(lines, heading)
        end = self._find_line_index(lines, boundary)
        if start is None or end is None or end <= start:
            return []

        section_lines = lines[start + 1 : end]
        header_end = self._find_header_end(
            section_lines,
            (
                'No',
                'Tender Title',
                'Tender Type',
                'Type of Offer',
                'Tender Duration',
                'Expected launch Date',
            ),
        )
        if header_end is None:
            return []

        data_lines = section_lines[header_end:]
        items: list[SaudiMohRawItem] = []
        index = 0
        while index < len(data_lines):
            if not data_lines[index].isdigit():
                index += 1
                continue

            if index + 5 >= len(data_lines):
                break

            title_text = data_lines[index + 1]
            tendering_date = data_lines[index + 5]
            if not title_text or not self._looks_like_date(tendering_date):
                index += 1
                continue

            raw_text = self._normalize_whitespace(
                ' '.join(
                    (
                        title_text,
                        data_lines[index + 2],
                        data_lines[index + 3],
                        data_lines[index + 4],
                        tendering_date,
                    )
                )
            )
            items.append(
                SaudiMohRawItem(
                    item_index=len(items),
                    extracted_at=extracted_at,
                    page_url=page_url,
                    source_section='planned_tenders',
                    title_text=title_text,
                    detail_url=None,
                    raw_text=raw_text,
                    visible_tender_number=None,
                    visible_tendering_date=tendering_date,
                    visible_bidding_deadline=None,
                    visible_opening_date=None,
                    visible_status=None,
                )
            )
            index += 6

        return items

    def _parse_submission_deadline_section(
        self,
        *,
        lines: list[str],
        page_url: str,
        extracted_at: datetime,
        start_index: int,
    ) -> list[SaudiMohRawItem]:
        """Parse the section that explicitly exposes submission deadlines."""
        marker_index = self._find_line_index(lines, 'Submission deadline')
        if marker_index is None:
            return []

        header_start = marker_index - 5
        if header_start < 0:
            return []

        data_lines = lines[marker_index + 1 :]
        boundary = self._find_line_index(data_lines, 'in this Section')
        if boundary is not None:
            data_lines = data_lines[:boundary]

        items: list[SaudiMohRawItem] = []
        index = 0
        while index < len(data_lines):
            if not data_lines[index].isdigit():
                index += 1
                continue

            if index + 5 >= len(data_lines):
                break

            title_text = data_lines[index + 1]
            tendering_date = data_lines[index + 4]
            bidding_deadline = data_lines[index + 5]
            if not title_text or not self._looks_like_date(tendering_date):
                index += 1
                continue
            if not self._looks_like_date(bidding_deadline):
                index += 1
                continue

            raw_text = self._normalize_whitespace(
                ' '.join(
                    (
                        title_text,
                        data_lines[index + 2],
                        data_lines[index + 3],
                        tendering_date,
                        bidding_deadline,
                    )
                )
            )
            items.append(
                SaudiMohRawItem(
                    item_index=start_index + len(items),
                    extracted_at=extracted_at,
                    page_url=page_url,
                    source_section='submission_deadline_tenders',
                    title_text=title_text,
                    detail_url=None,
                    raw_text=raw_text,
                    visible_tender_number=None,
                    visible_tendering_date=tendering_date,
                    visible_bidding_deadline=bidding_deadline,
                    visible_opening_date=None,
                    visible_status=None,
                )
            )
            index += 6

        return items

    @staticmethod
    def _find_line_index(lines: list[str], needle: str) -> int | None:
        """Locate one normalized line exactly."""
        normalized_needle = SaudiMohCrawler._normalize_whitespace(needle)
        for index, line in enumerate(lines):
            if SaudiMohCrawler._normalize_whitespace(line) == normalized_needle:
                return index
        return None

    def _find_header_end(self, lines: list[str], header_tokens: tuple[str, ...]) -> int | None:
        """Find the line index directly after a visible header token sequence."""
        normalized_lines = [self._normalize_whitespace(line) for line in lines]
        normalized_tokens = [self._normalize_whitespace(token) for token in header_tokens]
        for index in range(0, len(normalized_lines) - len(normalized_tokens) + 1):
            if normalized_lines[index : index + len(normalized_tokens)] == normalized_tokens:
                return index + len(normalized_tokens)
        return None

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
        cleaned = value.replace('\xa0', ' ').replace('T en der', 'Tender')
        cleaned = cleaned.replace('Expected launching date', 'Expected launch Date')
        cleaned = cleaned.replace('Expected launching date', 'Expected launch Date')
        return _WHITESPACE_RE.sub(' ', cleaned).strip()

    @classmethod
    def _to_lines(cls, body_text: str) -> list[str]:
        """Split body text into compact non-empty visible lines."""
        return [
            normalized
            for raw_line in body_text.splitlines()
            if (normalized := cls._normalize_whitespace(raw_line))
        ]

    @staticmethod
    def _looks_like_date(value: str | None) -> bool:
        """Return True when the visible text looks like an absolute English date."""
        if value is None:
            return False
        return _DATE_TEXT_RE.fullmatch(
            _WHITESPACE_RE.sub(' ', value.replace('\xa0', ' ')).strip()
        ) is not None


async def run_saudi_moh_crawl() -> SaudiMohCrawlResult:
    """Convenience entrypoint for one Saudi MOH crawl."""
    crawler = SaudiMohCrawler()
    return await crawler.crawl()
