from __future__ import annotations

import asyncio
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.bahrain_tender_board_config import (
	BAHRAIN_TENDER_BOARD_CONFIG,
)
from src.crawler.sources.bahrain_tender_board_crawler import (
	BahrainTenderBoardRawItem,
	run_bahrain_tender_board_crawl,
)

_WHITESPACE_RE = re.compile(r'\s+')
_REFERENCE_RE = re.compile(r'\b\d{1,6}/\d{4}/[A-Z]{2,8}\b')
_PAREN_VALUE_RE = re.compile(r'\(([^()\n]+)\)')
_DATE_VALUE_RE = re.compile(r'(?P<value>\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?)')
_LABEL_VALUE_PATTERNS: dict[str, re.Pattern[str]] = {
	'issuing_entity': re.compile(
		r'(?:purchasing authority|authority|entity|ministry|organization)\s*[:\-]?\s*(.+)',
		re.IGNORECASE,
	),
	'closing_date': re.compile(
		r'(?:closing date|submission date|submission deadline|bid closing|closing)\s*[:\-]?\s*(.+)',
		re.IGNORECASE,
	),
	'published_at': re.compile(
		r'(?:publication date|published date|publish date|issue date)\s*[:\-]?\s*(.+)',
		re.IGNORECASE,
	),
	'opening_date': re.compile(
		r'(?:opening date|technical opening|bid opening)\s*[:\-]?\s*(.+)',
		re.IGNORECASE,
	),
	'category': re.compile(
		r'(?:category|tender type|procurement type|type)\s*[:\-]?\s*(.+)',
		re.IGNORECASE,
	),
}
_DOCUMENT_TEXT_MARKERS: tuple[str, ...] = (
	'download',
	'document',
	'attachment',
	'pdf',
	'doc',
	'xls',
	'zip',
)
_SECURITY_PAGE_MARKERS: tuple[str, ...] = (
	'you are unable to access the requested page',
	'your session in the client area has expired',
	'you are attempting to access a page without signing in',
	'click here to login',
)


class BahrainTenderBoardDetailCrawlerError(RuntimeError):
	"""Base class for Bahrain Tender Board detail-page crawl failures."""


class BahrainTenderBoardDetailNavigationError(BahrainTenderBoardDetailCrawlerError):
	"""Raised when a Bahrain detail page cannot be loaded."""


class BahrainTenderBoardDetailAccessError(BahrainTenderBoardDetailCrawlerError):
	"""Raised when the Bahrain detail page is not publicly accessible."""


class BahrainTenderBoardDetailExtractionError(BahrainTenderBoardDetailCrawlerError):
	"""Raised when deterministic detail-page extraction cannot proceed."""


@dataclass(frozen=True)
class BahrainTenderBoardDetailItem:
	"""One sampled Bahrain detail page and any deterministic fields visible on it."""

	item_index: int
	extracted_at: datetime
	dashboard_title_text: str
	dashboard_visible_entity: str | None
	dashboard_visible_tender_number: str | None
	dashboard_visible_pa_reference: str | None
	dashboard_visible_time_left: str | None
	detail_url: str
	final_url: str
	detail_page_title: str
	access_status: str
	detail_title: str | None
	detail_issuing_entity: str | None
	detail_tender_number: str | None
	detail_pa_reference: str | None
	detail_closing_date_raw: str | None
	detail_published_at_raw: str | None
	detail_opening_date_raw: str | None
	detail_category: str | None
	detail_document_indicators: tuple[str, ...]
	stronger_fields: tuple[str, ...]
	raw_text: str


@dataclass(frozen=True)
class BahrainTenderBoardDetailCrawlResult:
	"""Structured summary of sampled Bahrain detail-page inspection."""

	source_name: str
	listing_url: str
	final_listing_url: str
	sample_count: int
	successful_detail_pages: int
	security_page_count: int
	extracted_at: datetime
	items: tuple[BahrainTenderBoardDetailItem, ...]


class BahrainTenderBoardDetailCrawler:
	"""
	Deterministic inspector for Bahrain Tender Board public detail pages.

	This slice exists only to answer one question:
	do the dashboard-derived public detail URLs expose stronger visible fields than
	the dashboard rows, or do they fail behind access control?
	"""

	USER_AGENT: Final[str] = (
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
	)

	def __init__(
		self,
		*,
		sample_size: int | None = 5,
		dashboard_items: Sequence[BahrainTenderBoardRawItem] | None = None,
	) -> None:
		self._config = BAHRAIN_TENDER_BOARD_CONFIG
		self._sample_size = None if sample_size is None else max(1, sample_size)
		self._dashboard_items = None if dashboard_items is None else tuple(dashboard_items)

	async def crawl(self) -> BahrainTenderBoardDetailCrawlResult:
		"""Inspect a small live sample of Bahrain public detail URLs."""
		listing_result = await run_bahrain_tender_board_crawl()
		source_items = self._dashboard_items or listing_result.items
		sampled_items = source_items if self._sample_size is None else source_items[: self._sample_size]
		if not sampled_items:
			raise BahrainTenderBoardDetailExtractionError('dashboard crawl returned no sample rows for detail inspection')

		async with async_playwright() as playwright:
			browser = await playwright.chromium.launch(headless=True)
			try:
				context = await self._new_context(browser)
				try:
					await self._prime_public_session(context)
					items: list[BahrainTenderBoardDetailItem] = []
					for item in sampled_items:
						items.append(await self._inspect_detail_page(context, item))
				finally:
					await context.close()
			finally:
				await browser.close()

		successful_detail_pages = sum(1 for item in items if item.access_status == 'detail_page')
		security_page_count = sum(1 for item in items if item.access_status == 'security_page')

		return BahrainTenderBoardDetailCrawlResult(
			source_name=listing_result.source_name,
			listing_url=listing_result.listing_url,
			final_listing_url=listing_result.final_url,
			sample_count=len(items),
			successful_detail_pages=successful_detail_pages,
			security_page_count=security_page_count,
			extracted_at=datetime.now(UTC),
			items=tuple(items),
		)

	async def _new_context(self, browser: Browser) -> BrowserContext:
		"""Create a browser context consistent with the listing crawler."""
		return await browser.new_context(
			user_agent=self.USER_AGENT,
			viewport={'width': 1440, 'height': 1200},
			java_script_enabled=True,
			locale='en-BH',
			timezone_id='Asia/Bahrain',
		)

	async def _prime_public_session(self, context: BrowserContext) -> None:
		"""
		Load the public dashboard first.

		The live site may rely on session state or referrer flow. We prime the same
		public dashboard used by the listing crawler before opening any detail pages.
		"""
		page = await context.new_page()
		try:
			response = await page.goto(
				self._config.listing_url,
				wait_until='domcontentloaded',
				timeout=self._config.page_load_timeout_ms,
			)
			if response is None or response.status >= 400:
				raise BahrainTenderBoardDetailNavigationError('failed to prime the Bahrain public dashboard session')
			await self._sleep_with_jitter()
		finally:
			await page.close()

	async def _inspect_detail_page(
		self,
		context: BrowserContext,
		dashboard_item: BahrainTenderBoardRawItem,
	) -> BahrainTenderBoardDetailItem:
		"""Open one detail URL and extract only clearly visible deterministic fields."""
		page = await context.new_page()
		try:
			try:
				response = await page.goto(
					dashboard_item.detail_url,
					wait_until='domcontentloaded',
					timeout=self._config.page_load_timeout_ms,
				)
			except Exception as exc:
				raise BahrainTenderBoardDetailNavigationError(
					f"failed to navigate to '{dashboard_item.detail_url}': {type(exc).__name__}: {exc}"
				) from exc

			if response is None:
				raise BahrainTenderBoardDetailNavigationError('detail navigation returned no HTTP response')
			if response.status >= 400:
				raise BahrainTenderBoardDetailNavigationError(f'detail navigation failed with HTTP status {response.status}')

			await self._sleep_with_jitter()
			detail_page_title = (await page.title()).strip()
			raw_text = await self._get_body_text(page)
			access_status = self._classify_access_status(detail_page_title, raw_text)

			if access_status == 'security_page':
				return BahrainTenderBoardDetailItem(
					item_index=dashboard_item.item_index,
					extracted_at=datetime.now(UTC),
					dashboard_title_text=dashboard_item.title_text,
					dashboard_visible_entity=dashboard_item.visible_entity,
					dashboard_visible_tender_number=dashboard_item.visible_tender_number,
					dashboard_visible_pa_reference=dashboard_item.visible_pa_reference,
					dashboard_visible_time_left=dashboard_item.visible_time_left,
					detail_url=dashboard_item.detail_url,
					final_url=page.url,
					detail_page_title=detail_page_title,
					access_status=access_status,
					detail_title=None,
					detail_issuing_entity=None,
					detail_tender_number=None,
					detail_pa_reference=None,
					detail_closing_date_raw=None,
					detail_published_at_raw=None,
					detail_opening_date_raw=None,
					detail_category=None,
					detail_document_indicators=(),
					stronger_fields=(),
					raw_text=raw_text,
				)

			detail_item = self._extract_visible_detail_fields(
				dashboard_item=dashboard_item,
				detail_page_title=detail_page_title,
				final_url=page.url,
				raw_text=raw_text,
				links=await self._extract_visible_links(page),
			)
			return detail_item
		finally:
			await page.close()

	async def _get_body_text(self, page: Page) -> str:
		"""Extract normalized body text for blocker detection and visible fields."""
		body_locator = page.locator(self._config.page_body)
		if await body_locator.count() == 0:
			raise BahrainTenderBoardDetailExtractionError('detail page body selector was not found')
		return self._normalize_whitespace(await body_locator.inner_text())

	async def _extract_visible_links(self, page: Page) -> tuple[tuple[str, str], ...]:
		"""
		Extract visible anchors from the detail page.

		This stays generic because the live public detail page is currently blocked
		from this environment, so no stable field-specific selectors are proven yet.
		"""
		links = await page.locator('a').evaluate_all(
			"""
            (elements) => elements
              .map((element) => {
                const text = (element.innerText || "").trim();
                const href = (element.getAttribute("href") || "").trim();
                const visible = !!(text || href);
                return visible ? { text, href } : null;
              })
              .filter(Boolean)
            """
		)
		normalized_links: list[tuple[str, str]] = []
		for link in links:
			text = self._normalize_whitespace(str(link.get('text', '')))
			href = self._normalize_whitespace(str(link.get('href', '')))
			if text or href:
				normalized_links.append((text, href))
		return tuple(normalized_links)

	def _classify_access_status(self, page_title: str, raw_text: str) -> str:
		"""Classify whether the detail URL yields a public detail page or a security page."""
		normalized_title = page_title.casefold()
		normalized_body = raw_text.casefold()
		if normalized_title == 'security page':
			return 'security_page'
		if any(marker in normalized_body for marker in _SECURITY_PAGE_MARKERS):
			return 'security_page'
		return 'detail_page'

	def _extract_visible_detail_fields(
		self,
		*,
		dashboard_item: BahrainTenderBoardRawItem,
		detail_page_title: str,
		final_url: str,
		raw_text: str,
		links: tuple[tuple[str, str], ...],
	) -> BahrainTenderBoardDetailItem:
		"""Extract only clearly visible deterministic detail-page fields."""
		detail_title = self._extract_detail_title(raw_text, dashboard_item.title_text)
		detail_issuing_entity = self._extract_labeled_value('issuing_entity', raw_text)
		detail_tender_number = self._extract_tender_number(raw_text)
		detail_pa_reference = self._extract_pa_reference(raw_text)
		detail_closing_date_raw = self._extract_labeled_date('closing_date', raw_text)
		detail_published_at_raw = self._extract_labeled_date('published_at', raw_text)
		detail_opening_date_raw = self._extract_labeled_date('opening_date', raw_text)
		detail_category = self._extract_labeled_value('category', raw_text)
		document_indicators = self._extract_document_indicators(links)
		stronger_fields = self._determine_stronger_fields(
			dashboard_item=dashboard_item,
			detail_title=detail_title,
			detail_issuing_entity=detail_issuing_entity,
			detail_pa_reference=detail_pa_reference,
			detail_closing_date_raw=detail_closing_date_raw,
			detail_published_at_raw=detail_published_at_raw,
			detail_opening_date_raw=detail_opening_date_raw,
			detail_category=detail_category,
			document_indicators=document_indicators,
		)

		return BahrainTenderBoardDetailItem(
			item_index=dashboard_item.item_index,
			extracted_at=datetime.now(UTC),
			dashboard_title_text=dashboard_item.title_text,
			dashboard_visible_entity=dashboard_item.visible_entity,
			dashboard_visible_tender_number=dashboard_item.visible_tender_number,
			dashboard_visible_pa_reference=dashboard_item.visible_pa_reference,
			dashboard_visible_time_left=dashboard_item.visible_time_left,
			detail_url=dashboard_item.detail_url,
			final_url=final_url,
			detail_page_title=detail_page_title,
			access_status='detail_page',
			detail_title=detail_title,
			detail_issuing_entity=detail_issuing_entity,
			detail_tender_number=detail_tender_number,
			detail_pa_reference=detail_pa_reference,
			detail_closing_date_raw=detail_closing_date_raw,
			detail_published_at_raw=detail_published_at_raw,
			detail_opening_date_raw=detail_opening_date_raw,
			detail_category=detail_category,
			detail_document_indicators=document_indicators,
			stronger_fields=stronger_fields,
			raw_text=raw_text,
		)

	def _extract_detail_title(self, raw_text: str, dashboard_title: str) -> str | None:
		"""Extract a stronger visible title only if it is clearly present."""
		dashboard_clean = dashboard_title.strip()
		for line in raw_text.splitlines():
			cleaned = line.strip('() ').strip()
			if not cleaned:
				continue
			if cleaned == dashboard_clean:
				return cleaned
			if dashboard_clean.endswith('.....') and cleaned.startswith(dashboard_clean[:-5]):
				return cleaned
		return None

	def _extract_tender_number(self, raw_text: str) -> str | None:
		"""Extract a visible tender number when explicitly shown on the detail page."""
		match = _REFERENCE_RE.search(raw_text)
		if match is None:
			return None
		return match.group(0)

	def _extract_pa_reference(self, raw_text: str) -> str | None:
		"""Extract a parenthesized PA reference only if it is visibly complete."""
		for line in raw_text.splitlines():
			match = _PAREN_VALUE_RE.search(line)
			if match is None:
				continue
			candidate = self._normalize_whitespace(match.group(1))
			if candidate and '...' not in candidate:
				return candidate
		return None

	def _extract_labeled_date(self, key: str, raw_text: str) -> str | None:
		"""Extract a labeled absolute date-like field from visible detail-page text."""
		labeled_value = self._extract_labeled_value(key, raw_text)
		if labeled_value is None:
			return None
		match = _DATE_VALUE_RE.search(labeled_value)
		if match is None:
			return None
		return match.group('value')

	def _extract_labeled_value(self, key: str, raw_text: str) -> str | None:
		"""Extract a labeled visible field from the detail-page body text."""
		pattern = _LABEL_VALUE_PATTERNS[key]
		for line in raw_text.splitlines():
			match = pattern.search(line)
			if match is None:
				continue
			value = self._normalize_whitespace(match.group(1))
			if value:
				return value
		return None

	def _extract_document_indicators(
		self,
		links: tuple[tuple[str, str], ...],
	) -> tuple[str, ...]:
		"""Return generic public document/download indicators visible on the page."""
		indicators: list[str] = []
		for text, href in links:
			normalized = f'{text} {href}'.casefold()
			if not any(marker in normalized for marker in _DOCUMENT_TEXT_MARKERS):
				continue
			label = text or href
			compact = self._normalize_whitespace(label)
			if compact and compact not in indicators:
				indicators.append(compact)
		return tuple(indicators)

	def _determine_stronger_fields(
		self,
		*,
		dashboard_item: BahrainTenderBoardRawItem,
		detail_title: str | None,
		detail_issuing_entity: str | None,
		detail_pa_reference: str | None,
		detail_closing_date_raw: str | None,
		detail_published_at_raw: str | None,
		detail_opening_date_raw: str | None,
		detail_category: str | None,
		document_indicators: tuple[str, ...],
	) -> tuple[str, ...]:
		"""Identify which fields became stronger on the detail page than on the dashboard."""
		stronger_fields: list[str] = []

		if detail_title is not None and detail_title != dashboard_item.title_text:
			stronger_fields.append('title')
		if dashboard_item.visible_entity is None and detail_issuing_entity is not None:
			stronger_fields.append('issuing_entity')
		if dashboard_item.visible_pa_reference is None and detail_pa_reference is not None:
			stronger_fields.append('pa_reference')
		if dashboard_item.visible_time_left is not None and detail_closing_date_raw is not None:
			stronger_fields.append('closing_date')
		if detail_published_at_raw is not None:
			stronger_fields.append('publication_date')
		if detail_opening_date_raw is not None:
			stronger_fields.append('opening_date')
		if detail_category is not None:
			stronger_fields.append('category')
		if document_indicators:
			stronger_fields.append('document_indicators')

		return tuple(stronger_fields)

	def _normalize_whitespace(self, value: str) -> str:
		"""Collapse repeated whitespace while preserving line boundaries."""
		collapsed_lines = [_WHITESPACE_RE.sub(' ', line).strip() for line in value.splitlines() if line.strip()]
		return '\n'.join(collapsed_lines)

	async def _sleep_with_jitter(self) -> None:
		"""Apply bounded deterministic-friendly jitter between actions."""
		jitter_ms = random.randint(
			self._config.min_jitter_ms,
			self._config.max_jitter_ms,
		)
		await asyncio.sleep(jitter_ms / 1000)


async def run_bahrain_tender_board_detail_crawl(
	*,
	sample_size: int | None = 5,
	dashboard_items: Sequence[BahrainTenderBoardRawItem] | None = None,
) -> BahrainTenderBoardDetailCrawlResult:
	"""Convenience entrypoint for live Bahrain detail-page inspection."""
	crawler = BahrainTenderBoardDetailCrawler(
		sample_size=sample_size,
		dashboard_items=dashboard_items,
	)
	return await crawler.crawl()
