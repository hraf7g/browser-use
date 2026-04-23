from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import parse_qsl, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.abu_dhabi_gpg_config import ABU_DHABI_GPG_CONFIG

_WHITESPACE_RE = re.compile(r"\s+")
_SUPPORT_ID_RE = re.compile(
    r"(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)",
    re.IGNORECASE,
)


class AbuDhabiGPGCrawlerError(RuntimeError):
    """Base class for Abu Dhabi GPG crawler failures."""


class AbuDhabiGPGNavigationError(AbuDhabiGPGCrawlerError):
    """Raised when the listing page cannot be loaded or verified."""


class AbuDhabiGPGBlockedError(AbuDhabiGPGCrawlerError):
    """Raised when the public page is blocked by anti-bot or access controls."""


class AbuDhabiGPGExtractionError(AbuDhabiGPGCrawlerError):
    """Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class AbuDhabiGPGRawItem:
    """
    Raw deterministic tender card extracted from the Abu Dhabi GPG public homepage.

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
    visible_due_date: str | None
    visible_category_label: str | None
    visible_notice_type: str | None
    visible_short_description: str | None


@dataclass(frozen=True)
class AbuDhabiGPGCrawlResult:
    """Structured result for one Abu Dhabi GPG public-page crawl."""

    source_name: str
    listing_url: str
    final_url: str
    page_title: str
    extracted_at: datetime
    total_items: int
    items: tuple[AbuDhabiGPGRawItem, ...]


class AbuDhabiGPGCrawler:
    """
    Deterministic crawler for the Abu Dhabi GPG public active-tenders widget.

    Scope:
        - navigate to the official public homepage
        - verify the page is the expected source and not an anti-bot wall
        - extract raw tender cards from the visible active-tenders widget
        - validate public detail URLs embedded in those cards
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
        self._config = ABU_DHABI_GPG_CONFIG

    async def crawl(self) -> AbuDhabiGPGCrawlResult:
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

                    return AbuDhabiGPGCrawlResult(
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
            locale="en-AE",
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
            raise AbuDhabiGPGNavigationError(
                f"failed to navigate to '{self._config.listing_url}': "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if response is None:
            raise AbuDhabiGPGNavigationError("navigation returned no HTTP response")

        if response.status >= 400:
            raise AbuDhabiGPGNavigationError(
                f"navigation failed with HTTP status {response.status}"
            )

        await self._sleep_with_jitter()

    async def _get_body_text(self, page: Page) -> str:
        """Extract full body text for verification and blocker detection."""
        body_locator = page.locator(self._config.page_body)
        if await body_locator.count() == 0:
            raise AbuDhabiGPGNavigationError("page body selector was not found")
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

        raise AbuDhabiGPGBlockedError(
            "anti-bot or access-control page detected"
            f"{support_suffix}; matched markers={matched_markers}"
        )

    def _verify_page(self, body_text: str) -> None:
        """Verify that expected public widget markers are present."""
        normalized_body = body_text.casefold()
        matched_markers = [
            marker
            for marker in self._config.expected_page_text_markers
            if marker.casefold() in normalized_body
        ]
        if not matched_markers:
            raise AbuDhabiGPGNavigationError(
                "page verification failed; expected Abu Dhabi GPG markers were not found"
            )

    async def _extract_items(self, page: Page) -> list[AbuDhabiGPGRawItem]:
        """Extract raw public tender cards from the homepage widget."""
        card_locator = page.locator(self._config.tender_cards)
        card_count = await card_locator.count()
        if card_count == 0:
            raise AbuDhabiGPGExtractionError("no active-tender cards were found")

        extracted_at = datetime.now(UTC)
        items: list[AbuDhabiGPGRawItem] = []
        seen_urls: set[str] = set()

        for card_index in range(card_count):
            card = card_locator.nth(card_index)
            href = await card.get_attribute("href")
            if not isinstance(href, str) or not href.strip():
                continue

            detail_url = self._validate_detail_url(href.strip())
            if detail_url in seen_urls:
                continue

            raw_text = self._normalize_whitespace(await card.inner_text())
            if not raw_text:
                continue

            title_text = await self._extract_optional_inner_text(card, self._config.card_title)
            if title_text is None:
                continue

            visible_due_date = await self._extract_optional_inner_text(card, self._config.card_date)
            visible_category_label = await self._extract_optional_inner_text(
                card,
                self._config.card_type_label,
            )
            visible_short_description = await self._extract_optional_inner_text(
                card,
                self._config.card_short_description,
            )

            items.append(
                AbuDhabiGPGRawItem(
                    item_index=len(items),
                    extracted_at=extracted_at,
                    page_url=page.url,
                    title_text=title_text,
                    detail_url=detail_url,
                    raw_text=raw_text,
                    visible_due_date=visible_due_date,
                    visible_category_label=visible_category_label,
                    visible_notice_type=self._extract_visible_notice_type(title_text),
                    visible_short_description=visible_short_description,
                )
            )
            seen_urls.add(detail_url)

        if not items:
            raise AbuDhabiGPGExtractionError(
                "active-tender cards were found, but no non-empty raw items could be extracted"
            )

        return items

    async def _extract_optional_inner_text(self, container, selector: str) -> str | None:
        """Extract optional inner text from a descendant selector."""
        locator = container.locator(selector).first
        if await locator.count() == 0:
            return None
        value = self._normalize_whitespace(await locator.inner_text())
        return value or None

    def _extract_visible_notice_type(self, title_text: str) -> str | None:
        """Extract a visible notice-type prefix such as RFQ or RFI when present."""
        cleaned = title_text.strip()
        if not cleaned:
            return None
        prefix = cleaned.split("-", 1)[0].strip()
        if not prefix:
            return None
        if len(prefix) <= 12 and prefix.upper() == prefix:
            return prefix
        return None

    def _validate_detail_url(self, detail_url: str) -> str:
        """Validate that the detail URL stays on the expected public tender route."""
        parsed = urlparse(detail_url)
        if parsed.scheme != "https":
            raise AbuDhabiGPGExtractionError("detail URL is not https")
        if parsed.netloc != "www.adgpg.gov.ae":
            raise AbuDhabiGPGExtractionError(
                "detail URL does not stay on www.adgpg.gov.ae"
            )
        if parsed.path != "/en/For-Suppliers/Public-Tenders":
            raise AbuDhabiGPGExtractionError(
                "detail URL path is not the expected public-tender route"
            )

        query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if not query_pairs.get("id"):
            raise AbuDhabiGPGExtractionError(
                "detail URL is missing a non-empty public tender id query parameter"
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

    async def _sleep_with_jitter(self) -> None:
        """Apply bounded deterministic-friendly jitter between actions."""
        jitter_ms = random.randint(
            self._config.min_jitter_ms,
            self._config.max_jitter_ms,
        )
        await asyncio.sleep(jitter_ms / 1000)


async def run_abu_dhabi_gpg_crawl() -> AbuDhabiGPGCrawlResult:
    """Convenience entrypoint for programmatic verification."""
    crawler = AbuDhabiGPGCrawler()
    return await crawler.crawl()
