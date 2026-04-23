from __future__ import annotations

import asyncio
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.abu_dhabi_gpg_config import ABU_DHABI_GPG_CONFIG
from src.crawler.sources.abu_dhabi_gpg_crawler import (
    AbuDhabiGPGRawItem,
    run_abu_dhabi_gpg_crawl,
)

_WHITESPACE_RE = re.compile(r"\s+")
_SUPPORT_ID_RE = re.compile(
    r"(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)",
    re.IGNORECASE,
)
_BLOCKED_TEXT_MARKERS: tuple[str, ...] = (
    "your request could not be processed",
    "request rejected",
    "support id",
    "reference id",
    "access denied",
)
_DOCUMENT_TEXT_MARKERS: tuple[str, ...] = (
    "download",
    "document",
    "attachment",
    "pdf",
    "doc",
    "xls",
    "zip",
)
_PUBLIC_ACTION_MARKERS: tuple[str, ...] = (
    "get updates on this tender",
    "share",
    "print",
    "participate now",
)


class AbuDhabiGPGDetailCrawlerError(RuntimeError):
    """Base class for Abu Dhabi GPG detail-page crawl failures."""


class AbuDhabiGPGDetailNavigationError(AbuDhabiGPGDetailCrawlerError):
    """Raised when an Abu Dhabi GPG detail page cannot be loaded."""


class AbuDhabiGPGDetailAccessError(AbuDhabiGPGDetailCrawlerError):
    """Raised when an Abu Dhabi GPG detail page is blocked or inaccessible."""


class AbuDhabiGPGDetailExtractionError(AbuDhabiGPGDetailCrawlerError):
    """Raised when deterministic detail-page extraction cannot proceed."""


@dataclass(frozen=True)
class AbuDhabiGPGDetailItem:
    """One sampled Abu Dhabi GPG detail page and its deterministic visible fields."""

    item_index: int
    extracted_at: datetime
    widget_title_text: str
    widget_visible_due_date: str | None
    widget_visible_category_label: str | None
    widget_visible_notice_type: str | None
    widget_visible_short_description: str | None
    detail_url: str
    final_url: str
    detail_page_title: str
    access_status: str
    detail_title: str | None
    detail_issuing_entity: str | None
    detail_tender_ref: str | None
    detail_closing_date_raw: str | None
    detail_published_at_raw: str | None
    detail_opening_date_raw: str | None
    detail_category: str | None
    detail_notice_type: str | None
    detail_description: str | None
    detail_document_indicators: tuple[str, ...]
    detail_public_action_indicators: tuple[str, ...]
    stronger_fields: tuple[str, ...]
    raw_text: str


@dataclass(frozen=True)
class AbuDhabiGPGDetailCrawlResult:
    """Structured summary of sampled Abu Dhabi GPG detail-page inspection."""

    source_name: str
    listing_url: str
    final_listing_url: str
    sample_count: int
    successful_detail_pages: int
    blocked_page_count: int
    enrichment_supported: bool
    extracted_at: datetime
    items: tuple[AbuDhabiGPGDetailItem, ...]


class AbuDhabiGPGDetailCrawler:
    """
    Deterministic inspector for Abu Dhabi GPG public detail pages.

    This slice exists only to answer one question:
    do the homepage-widget detail URLs expose stronger visible fields than the
    widget cards themselves?
    """

    USER_AGENT: Final[str] = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        *,
        sample_size: int | None = 5,
        jitter_range_ms: tuple[int, int] | None = None,
    ) -> None:
        self._config = ABU_DHABI_GPG_CONFIG
        self._sample_size = None if sample_size is None else max(1, sample_size)
        self._jitter_range_ms = (
            (
                self._config.min_jitter_ms,
                self._config.max_jitter_ms,
            )
            if jitter_range_ms is None
            else jitter_range_ms
        )

    async def crawl(
        self,
        *,
        widget_items: Sequence[AbuDhabiGPGRawItem] | None = None,
    ) -> AbuDhabiGPGDetailCrawlResult:
        """Inspect sampled or full Abu Dhabi GPG public detail URLs."""
        if widget_items is None:
            listing_result = await run_abu_dhabi_gpg_crawl()
            listing_items = listing_result.items
            source_name = listing_result.source_name
            listing_url = listing_result.listing_url
            final_listing_url = listing_result.final_url
        else:
            listing_items = tuple(widget_items)
            source_name = self._config.source_name
            listing_url = self._config.listing_url
            final_listing_url = self._config.listing_url

        sampled_items = (
            listing_items
            if self._sample_size is None
            else listing_items[: self._sample_size]
        )
        if not sampled_items:
            raise AbuDhabiGPGDetailExtractionError(
                "widget crawl returned no sample rows for detail inspection"
            )

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                context = await self._new_context(browser)
                try:
                    items = []
                    for item in sampled_items:
                        try:
                            detail_item = await self._inspect_detail_page(context, item)
                        except AbuDhabiGPGDetailCrawlerError as exc:
                            detail_item = self._build_unavailable_detail_item(
                                widget_item=item,
                                failure_reason=str(exc),
                            )
                        items.append(detail_item)
                finally:
                    await context.close()
            finally:
                await browser.close()

        successful_detail_pages = sum(
            1 for item in items if item.access_status == "detail_page"
        )
        blocked_page_count = sum(1 for item in items if item.access_status == "blocked_page")
        enrichment_supported = any(bool(item.stronger_fields) for item in items)

        return AbuDhabiGPGDetailCrawlResult(
            source_name=source_name,
            listing_url=listing_url,
            final_listing_url=final_listing_url,
            sample_count=len(items),
            successful_detail_pages=successful_detail_pages,
            blocked_page_count=blocked_page_count,
            enrichment_supported=enrichment_supported,
            extracted_at=datetime.now(UTC),
            items=tuple(items),
        )

    async def _new_context(self, browser: Browser) -> BrowserContext:
        """Create a browser context consistent with the listing crawler."""
        return await browser.new_context(
            user_agent=self.USER_AGENT,
            viewport={"width": 1440, "height": 1200},
            java_script_enabled=True,
            locale="en-AE",
            timezone_id="Asia/Dubai",
        )

    async def _inspect_detail_page(
        self,
        context: BrowserContext,
        widget_item: AbuDhabiGPGRawItem,
    ) -> AbuDhabiGPGDetailItem:
        """Open one detail URL and extract only clearly visible deterministic fields."""
        page = await context.new_page()
        try:
            try:
                response = await page.goto(
                    widget_item.detail_url,
                    wait_until="domcontentloaded",
                    timeout=self._config.page_load_timeout_ms,
                )
            except Exception as exc:
                raise AbuDhabiGPGDetailNavigationError(
                    f"failed to navigate to '{widget_item.detail_url}': "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

            if response is None:
                raise AbuDhabiGPGDetailNavigationError(
                    "detail navigation returned no HTTP response"
                )
            if response.status >= 400:
                raise AbuDhabiGPGDetailNavigationError(
                    f"detail navigation failed with HTTP status {response.status}"
                )

            await self._sleep_with_jitter()
            detail_page_title = (await page.title()).strip()
            raw_text = await self._get_body_text(page)

            if self._is_blocked_page(detail_page_title, raw_text):
                return AbuDhabiGPGDetailItem(
                    item_index=widget_item.item_index,
                    extracted_at=datetime.now(UTC),
                    widget_title_text=widget_item.title_text,
                    widget_visible_due_date=widget_item.visible_due_date,
                    widget_visible_category_label=widget_item.visible_category_label,
                    widget_visible_notice_type=widget_item.visible_notice_type,
                    widget_visible_short_description=widget_item.visible_short_description,
                    detail_url=widget_item.detail_url,
                    final_url=page.url,
                    detail_page_title=detail_page_title,
                    access_status="blocked_page",
                    detail_title=None,
                    detail_issuing_entity=None,
                    detail_tender_ref=None,
                    detail_closing_date_raw=None,
                    detail_published_at_raw=None,
                    detail_opening_date_raw=None,
                    detail_category=None,
                    detail_notice_type=None,
                    detail_description=None,
                    detail_document_indicators=(),
                    detail_public_action_indicators=(),
                    stronger_fields=(),
                    raw_text=raw_text,
                )

            detail_item = await self._extract_visible_detail_fields(
                page=page,
                widget_item=widget_item,
                detail_page_title=detail_page_title,
                final_url=page.url,
                raw_text=raw_text,
            )
            return detail_item
        finally:
            await page.close()

    def _build_unavailable_detail_item(
        self,
        *,
        widget_item: AbuDhabiGPGRawItem,
        failure_reason: str,
    ) -> AbuDhabiGPGDetailItem:
        """Return a deterministic blocked-page item when one detail URL cannot be enriched."""
        return AbuDhabiGPGDetailItem(
            item_index=widget_item.item_index,
            extracted_at=datetime.now(UTC),
            widget_title_text=widget_item.title_text,
            widget_visible_due_date=widget_item.visible_due_date,
            widget_visible_category_label=widget_item.visible_category_label,
            widget_visible_notice_type=widget_item.visible_notice_type,
            widget_visible_short_description=widget_item.visible_short_description,
            detail_url=widget_item.detail_url,
            final_url=widget_item.detail_url,
            detail_page_title="Unavailable detail page",
            access_status="blocked_page",
            detail_title=None,
            detail_issuing_entity=None,
            detail_tender_ref=None,
            detail_closing_date_raw=None,
            detail_published_at_raw=None,
            detail_opening_date_raw=None,
            detail_category=None,
            detail_notice_type=None,
            detail_description=None,
            detail_document_indicators=(),
            detail_public_action_indicators=(),
            stronger_fields=(),
            raw_text=self._normalize_whitespace(failure_reason),
        )

    async def _extract_visible_detail_fields(
        self,
        *,
        page: Page,
        widget_item: AbuDhabiGPGRawItem,
        detail_page_title: str,
        final_url: str,
        raw_text: str,
    ) -> AbuDhabiGPGDetailItem:
        """Extract only clearly visible fields from the public detail block."""
        detail_section = page.locator(".sectionLoadedTender").first
        if await detail_section.count() == 0:
            raise AbuDhabiGPGDetailExtractionError(
                "detail page loaded, but the visible tender detail block was not found"
            )

        section_text = self._normalize_whitespace(await detail_section.inner_text())
        if not section_text:
            raise AbuDhabiGPGDetailExtractionError("detail block was empty")

        lines = [line for line in section_text.splitlines() if line]
        detail_tender_ref = await self._extract_optional_inner_text(
            detail_section,
            ".doc-number",
        )
        if detail_tender_ref is None and lines:
            detail_tender_ref = lines[0]

        detail_title = self._extract_line_after(
            lines,
            after_value=detail_tender_ref,
        )
        detail_issuing_entity = self._extract_entity_line(lines)
        detail_opening_date_raw = self._extract_label_value(lines, "BIDDING OPENS ON:")
        detail_closing_date_raw = self._extract_label_value(lines, "DUE ON:")
        detail_notice_type = self._extract_prefixed_value(lines, prefix="Event Type ")
        detail_category = self._extract_label_value(lines, "CATEGORY:")
        if detail_category is None:
            detail_category = detail_notice_type
        detail_description = self._extract_description(
            lines=lines,
            detail_title=detail_title,
            detail_issuing_entity=detail_issuing_entity,
            detail_tender_ref=detail_tender_ref,
            detail_category=detail_category,
        )
        detail_document_indicators = self._extract_text_indicators(
            section_text,
            markers=_DOCUMENT_TEXT_MARKERS,
        )
        detail_public_action_indicators = self._extract_text_indicators(
            section_text,
            markers=_PUBLIC_ACTION_MARKERS,
        )

        stronger_fields = self._build_stronger_fields(
            widget_item=widget_item,
            detail_title=detail_title,
            detail_issuing_entity=detail_issuing_entity,
            detail_tender_ref=detail_tender_ref,
            detail_closing_date_raw=detail_closing_date_raw,
            detail_opening_date_raw=detail_opening_date_raw,
            detail_category=detail_category,
            detail_notice_type=detail_notice_type,
            detail_description=detail_description,
        )

        return AbuDhabiGPGDetailItem(
            item_index=widget_item.item_index,
            extracted_at=datetime.now(UTC),
            widget_title_text=widget_item.title_text,
            widget_visible_due_date=widget_item.visible_due_date,
            widget_visible_category_label=widget_item.visible_category_label,
            widget_visible_notice_type=widget_item.visible_notice_type,
            widget_visible_short_description=widget_item.visible_short_description,
            detail_url=widget_item.detail_url,
            final_url=final_url,
            detail_page_title=detail_page_title,
            access_status="detail_page",
            detail_title=detail_title,
            detail_issuing_entity=detail_issuing_entity,
            detail_tender_ref=detail_tender_ref,
            detail_closing_date_raw=detail_closing_date_raw,
            detail_published_at_raw=None,
            detail_opening_date_raw=detail_opening_date_raw,
            detail_category=detail_category,
            detail_notice_type=detail_notice_type,
            detail_description=detail_description,
            detail_document_indicators=detail_document_indicators,
            detail_public_action_indicators=detail_public_action_indicators,
            stronger_fields=stronger_fields,
            raw_text=section_text,
        )

    async def _get_body_text(self, page: Page) -> str:
        """Extract full body text for blocker detection and diagnostics."""
        body_locator = page.locator(self._config.page_body)
        if await body_locator.count() == 0:
            raise AbuDhabiGPGDetailNavigationError("page body selector was not found")
        return await body_locator.inner_text()

    async def _extract_optional_inner_text(self, container, selector: str) -> str | None:
        """Extract optional inner text from a descendant selector."""
        locator = container.locator(selector).first
        if await locator.count() == 0:
            return None
        value = self._normalize_whitespace(await locator.inner_text())
        return value or None

    def _extract_label_value(self, lines: list[str], label: str) -> str | None:
        """Return the first non-empty line immediately following a visible label."""
        try:
            label_index = lines.index(label)
        except ValueError:
            return None

        for next_line in lines[label_index + 1 :]:
            if next_line:
                return next_line
        return None

    def _extract_prefixed_value(self, lines: list[str], *, prefix: str) -> str | None:
        """Extract a visible field from a line that starts with a fixed prefix."""
        for line in lines:
            if line.startswith(prefix):
                value = line.removeprefix(prefix).strip()
                return value or None
        return None

    def _extract_line_after(
        self,
        lines: list[str],
        *,
        after_value: str | None,
    ) -> str | None:
        """Return the first content line after a known visible line value."""
        if after_value is None:
            return None
        try:
            start_index = lines.index(after_value)
        except ValueError:
            return None

        for line in lines[start_index + 1 :]:
            if not line:
                continue
            if self._looks_like_relative_closing_text(line):
                continue
            return line
        return None

    def _extract_entity_line(self, lines: list[str]) -> str | None:
        """Extract the visible entity line from the detail block when present."""
        for index, line in enumerate(lines):
            if self._looks_like_relative_closing_text(line):
                if index > 0:
                    candidate = lines[index - 1].strip()
                    return candidate or None
        return None

    def _extract_description(
        self,
        *,
        lines: list[str],
        detail_title: str | None,
        detail_issuing_entity: str | None,
        detail_tender_ref: str | None,
        detail_category: str | None,
    ) -> str | None:
        """
        Extract a public description line only when it is clearly visible.

        ADGPG detail pages currently appear to expose title/entity/date/meta/action rows,
        not a reliable long-form scope block, so this returns None unless a distinct
        free-text line is visibly present before the metadata/action region.
        """
        ignored_lines = {
            detail_tender_ref,
            detail_title,
            detail_issuing_entity,
            "BIDDING OPENS ON:",
            "DUE ON:",
            "CATEGORY:",
            "Get updates on this tender",
            "Share",
            "Print",
            "PARTICIPATE NOW",
        }

        for line in lines:
            if line in ignored_lines:
                continue
            if self._looks_like_relative_closing_text(line):
                continue
            if line.startswith("Event Type "):
                continue
            if line.startswith("Estimated Value "):
                continue
            if self._looks_like_date_text(line):
                continue
            if detail_title is not None and line == detail_title:
                continue
            if detail_issuing_entity is not None and line == detail_issuing_entity:
                continue
            if detail_tender_ref is not None and line == detail_tender_ref:
                continue
            if detail_category is not None and line == detail_category:
                continue
            if line.endswith(":"):
                continue
            if line == "Recommended Tenders":
                continue
            if line in {"OPEN", "CLOSED"}:
                continue
            return line
        return None

    def _extract_text_indicators(
        self,
        text: str,
        *,
        markers: tuple[str, ...],
    ) -> tuple[str, ...]:
        """Return deterministic public indicators found verbatim in visible text."""
        normalized_text = text.casefold()
        return tuple(marker for marker in markers if marker in normalized_text)

    def _build_stronger_fields(
        self,
        *,
        widget_item: AbuDhabiGPGRawItem,
        detail_title: str | None,
        detail_issuing_entity: str | None,
        detail_tender_ref: str | None,
        detail_closing_date_raw: str | None,
        detail_opening_date_raw: str | None,
        detail_category: str | None,
        detail_notice_type: str | None,
        detail_description: str | None,
    ) -> tuple[str, ...]:
        """Return which fields became stronger on detail pages versus the widget."""
        stronger_fields: list[str] = []

        if detail_title is not None and detail_title != widget_item.title_text:
            stronger_fields.append("detail_title")
        if detail_issuing_entity is not None:
            stronger_fields.append("issuing_entity")
        if detail_tender_ref is not None:
            stronger_fields.append("tender_ref")
        if detail_closing_date_raw is not None and widget_item.visible_due_date is None:
            stronger_fields.append("closing_date")
        elif (
            detail_closing_date_raw is not None
            and widget_item.visible_due_date is not None
            and detail_closing_date_raw != widget_item.visible_due_date
        ):
            stronger_fields.append("closing_date")
        if detail_opening_date_raw is not None:
            stronger_fields.append("opening_date")
        if detail_category is not None and detail_category != widget_item.visible_category_label:
            stronger_fields.append("category_or_notice_type")
        elif (
            detail_notice_type is not None
            and widget_item.visible_notice_type is None
        ):
            stronger_fields.append("category_or_notice_type")
        if detail_description is not None and detail_description != widget_item.visible_short_description:
            stronger_fields.append("description")

        deduped: list[str] = []
        for field in stronger_fields:
            if field not in deduped:
                deduped.append(field)
        return tuple(deduped)

    def _is_blocked_page(self, detail_page_title: str, raw_text: str) -> bool:
        """Return whether the detail page looks blocked or request-rejected."""
        normalized = f"{detail_page_title}\n{raw_text}".casefold()
        if any(marker in normalized for marker in _BLOCKED_TEXT_MARKERS):
            return True
        return _SUPPORT_ID_RE.search(raw_text) is not None

    def _looks_like_relative_closing_text(self, value: str) -> bool:
        """Return whether a line matches the relative 'Closing in N Days' banner."""
        return value.casefold().startswith("closing in ")

    def _looks_like_date_text(self, value: str) -> bool:
        """Return whether a line looks like a visible absolute date."""
        try:
            datetime.strptime(value, "%d %B %Y")
        except ValueError:
            return False
        return True

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
        min_jitter_ms, max_jitter_ms = self._jitter_range_ms
        if min_jitter_ms <= 0 and max_jitter_ms <= 0:
            return

        if min_jitter_ms > max_jitter_ms:
            raise ValueError("jitter_range_ms min value must not exceed max value")

        jitter_ms = random.randint(min_jitter_ms, max_jitter_ms)
        await asyncio.sleep(jitter_ms / 1000)


async def run_abu_dhabi_gpg_detail_crawl(
    *,
    sample_size: int | None = 5,
    widget_items: Sequence[AbuDhabiGPGRawItem] | None = None,
    jitter_range_ms: tuple[int, int] | None = None,
) -> AbuDhabiGPGDetailCrawlResult:
    """Convenience entrypoint for programmatic verification."""
    crawler = AbuDhabiGPGDetailCrawler(
        sample_size=sample_size,
        jitter_range_ms=jitter_range_ms,
    )
    return await crawler.crawl(widget_items=widget_items)
