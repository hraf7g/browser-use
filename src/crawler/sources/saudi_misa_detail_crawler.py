from __future__ import annotations

import asyncio
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.saudi_misa_crawler import SaudiMisaRawItem, run_saudi_misa_crawl

_WHITESPACE_RE = re.compile(r'\s+')
_SUPPORT_ID_RE = re.compile(
	r'(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)',
	re.IGNORECASE,
)
_BLOCKED_TEXT_MARKERS: tuple[str, ...] = (
	'this question is for testing whether you are a human visitor',
	'prevent automated spam submission',
	'what code is in the image',
	'please enable javascript to view the page content',
	'your support id is',
	'captcha',
	'access denied',
)
_DOCUMENT_TEXT_MARKERS: tuple[str, ...] = (
	'مرفقات',
	'تحميل',
	'attachment',
	'download',
	'pdf',
	'doc',
	'xls',
	'zip',
)
_PUBLIC_ACTION_MARKERS: tuple[str, ...] = (
	'تقديم',
	'عرض',
	'details',
	'submit',
	'download',
)
_LABEL_VALUE_PATTERNS: dict[str, re.Pattern[str]] = {
	'title': re.compile(r'(?:إسم|اسم)\s+المنافسة\s*[:：]?\s*([^\n]+)'),
	'issuing_entity': re.compile(r'الجهة\s+الحكومية\s*[:：]?\s*([^\n]+)'),
	'tender_ref': re.compile(r'رقم\s+المنافسة\s*[:：]?\s*([^\n]+)'),
	'closing_date': re.compile(
		r'اخر\s+موعد\s+لإستلام\s+العروض[^\n]*?(?:الموافق\s*[:：]?\s*(\d{2}/\d{2}/\d{4}))',
		re.IGNORECASE,
	),
	'opening_date': re.compile(
		r'تاريخ\s+و\s*وقت\s+فتح\s+العروض[^\n]*?(?:الموافق\s*[:：]?\s*(\d{2}/\d{2}/\d{4}))',
		re.IGNORECASE,
	),
	'published_at': re.compile(
		r'اخر\s+موعد\s+لإستلام\s+استفسارات\s+الموردين[^\n]*?(?:الموافق\s*[:：]?\s*(\d{2}/\d{2}/\d{4}))',
		re.IGNORECASE,
	),
	'procurement_type': re.compile(r'نوع\s+المنافسة\s*[:：]?\s*([^\n]+)'),
}
_CLASSIFICATION_BLOCK_RE = re.compile(
	r'مجال\s+التصنيف\s*[:：]?\s*(?P<value>.*?)(?:مكان\s+التنفيذ|مكان\s+فتح\s+العروض|$)',
	re.DOTALL,
)
_CLASSIFICATION_BULLET_RE = re.compile(r'[•\-\*]?\s*([^\n]+)')


class SaudiMisaDetailCrawlerError(RuntimeError):
	"""Base class for Saudi MISA detail-page crawl failures."""


class SaudiMisaDetailNavigationError(SaudiMisaDetailCrawlerError):
	"""Raised when a Saudi MISA-linked Etimad detail page cannot be loaded."""


class SaudiMisaDetailAccessError(SaudiMisaDetailCrawlerError):
	"""Raised when a Saudi MISA-linked Etimad detail page is blocked or inaccessible."""


class SaudiMisaDetailExtractionError(SaudiMisaDetailCrawlerError):
	"""Raised when deterministic detail-page extraction cannot proceed."""


@dataclass(frozen=True)
class SaudiMisaDetailItem:
	"""One sampled Saudi MISA-linked Etimad detail page and its visible fields."""

	item_index: int
	extracted_at: datetime
	table_title_text: str
	table_reference_number: str | None
	table_inquiry_deadline_primary: str | None
	table_inquiry_deadline_secondary: str | None
	table_offer_opening_primary: str | None
	table_offer_opening_secondary: str | None
	table_status_link_text: str | None
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
	detail_procurement_type: str | None
	detail_description: str | None
	detail_document_indicators: tuple[str, ...]
	detail_public_action_indicators: tuple[str, ...]
	stronger_fields: tuple[str, ...]
	raw_text: str


@dataclass(frozen=True)
class SaudiMisaDetailCrawlResult:
	"""Structured summary of sampled Saudi MISA-linked detail-page inspection."""

	source_name: str
	listing_url: str
	final_listing_url: str
	sample_count: int
	successful_detail_pages: int
	blocked_page_count: int
	enrichment_supported: bool
	extracted_at: datetime
	items: tuple[SaudiMisaDetailItem, ...]


class SaudiMisaDetailCrawler:
	"""
	Deterministic inspector for Saudi MISA-linked Etimad public detail pages.

	This slice exists only to answer one question:
	do the visible Etimad detail URLs linked from the MISA table expose stronger
	deterministic fields than the MISA table itself from this environment?
	"""

	USER_AGENT: Final[str] = (
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
	)
	PAGE_LOAD_TIMEOUT_MS: Final[int] = 120_000
	MIN_JITTER_MS: Final[int] = 4_000
	MAX_JITTER_MS: Final[int] = 7_000

	def __init__(
		self,
		*,
		sample_size: int | None = 5,
		dashboard_items: Sequence[SaudiMisaRawItem] | None = None,
	) -> None:
		self._sample_size = None if sample_size is None else max(1, sample_size)
		self._dashboard_items = None if dashboard_items is None else tuple(dashboard_items)

	async def crawl(self) -> SaudiMisaDetailCrawlResult:
		"""Inspect a small live sample of Etimad detail URLs from the MISA table."""
		listing_result = await run_saudi_misa_crawl()
		source_items = self._dashboard_items or listing_result.items
		sampled_items = source_items if self._sample_size is None else source_items[: self._sample_size]
		if not sampled_items:
			raise SaudiMisaDetailExtractionError('misa table crawl returned no sample rows for detail inspection')

		async with async_playwright() as playwright:
			browser = await playwright.chromium.launch(headless=True)
			try:
				context = await self._new_context(browser)
				try:
					items = [await self._inspect_detail_page(context, item) for item in sampled_items]
				finally:
					await context.close()
			finally:
				await browser.close()

		successful_detail_pages = sum(1 for item in items if item.access_status == 'detail_page')
		blocked_page_count = sum(1 for item in items if item.access_status == 'blocked_page')
		enrichment_supported = any(bool(item.stronger_fields) for item in items)

		return SaudiMisaDetailCrawlResult(
			source_name=listing_result.source_name,
			listing_url=listing_result.listing_url,
			final_listing_url=listing_result.final_url,
			sample_count=len(items),
			successful_detail_pages=successful_detail_pages,
			blocked_page_count=blocked_page_count,
			enrichment_supported=enrichment_supported,
			extracted_at=datetime.now(UTC),
			items=tuple(items),
		)

	async def _new_context(self, browser: Browser) -> BrowserContext:
		"""Create a browser context suitable for Etimad public detail inspection."""
		return await browser.new_context(
			user_agent=self.USER_AGENT,
			viewport={'width': 1440, 'height': 1200},
			java_script_enabled=True,
			locale='ar-SA',
			timezone_id='Asia/Riyadh',
		)

	async def _inspect_detail_page(
		self,
		context: BrowserContext,
		table_item: SaudiMisaRawItem,
	) -> SaudiMisaDetailItem:
		"""Open one visible Etimad detail URL and extract deterministic fields only."""
		page = await context.new_page()
		try:
			try:
				response = await page.goto(
					table_item.detail_url,
					wait_until='domcontentloaded',
					timeout=self.PAGE_LOAD_TIMEOUT_MS,
				)
			except Exception as exc:
				raise SaudiMisaDetailNavigationError(
					f"failed to navigate to '{table_item.detail_url}': {type(exc).__name__}: {exc}"
				) from exc

			if response is None:
				raise SaudiMisaDetailNavigationError('detail navigation returned no HTTP response')
			if response.status >= 400:
				raise SaudiMisaDetailNavigationError(f'detail navigation failed with HTTP status {response.status}')

			await self._sleep_with_jitter()
			detail_page_title = (await page.title()).strip() or 'Untitled Etimad Detail Page'
			raw_text = await self._get_body_text(page)

			if self._is_blocked_page(detail_page_title, raw_text):
				return SaudiMisaDetailItem(
					item_index=table_item.item_index,
					extracted_at=datetime.now(UTC),
					table_title_text=table_item.title_text,
					table_reference_number=table_item.visible_reference_number,
					table_inquiry_deadline_primary=table_item.visible_offering_date,
					table_inquiry_deadline_secondary=table_item.visible_bid_deadline,
					table_offer_opening_primary=table_item.visible_inquiry_deadline,
					table_offer_opening_secondary=table_item.visible_bid_deadline,
					table_status_link_text=table_item.visible_status_link_text,
					detail_url=table_item.detail_url,
					final_url=page.url,
					detail_page_title=detail_page_title,
					access_status='blocked_page',
					detail_title=None,
					detail_issuing_entity=None,
					detail_tender_ref=None,
					detail_closing_date_raw=None,
					detail_published_at_raw=None,
					detail_opening_date_raw=None,
					detail_category=None,
					detail_procurement_type=None,
					detail_description=None,
					detail_document_indicators=(),
					detail_public_action_indicators=(),
					stronger_fields=(),
					raw_text=raw_text,
				)

			detail_item = await self._extract_visible_detail_fields(
				page=page,
				table_item=table_item,
				detail_page_title=detail_page_title,
				final_url=page.url,
				raw_text=raw_text,
			)
			return detail_item
		finally:
			await page.close()

	async def _extract_visible_detail_fields(
		self,
		*,
		page: Page,
		table_item: SaudiMisaRawItem,
		detail_page_title: str,
		final_url: str,
		raw_text: str,
	) -> SaudiMisaDetailItem:
		"""Extract only clearly visible fields from a reachable detail page."""
		body_text = self._normalize_whitespace(raw_text)
		if not body_text:
			raise SaudiMisaDetailExtractionError('detail page body was empty')

		detail_title = self._extract_labeled_value('title', body_text)
		detail_issuing_entity = self._extract_labeled_value('issuing_entity', body_text)
		detail_tender_ref = self._extract_labeled_value('tender_ref', body_text)
		detail_closing_date_raw = self._extract_labeled_value('closing_date', body_text)
		detail_published_at_raw = self._extract_labeled_value('published_at', body_text)
		detail_opening_date_raw = self._extract_labeled_value('opening_date', body_text)
		detail_category = self._extract_classification(body_text)
		detail_procurement_type = self._extract_labeled_value('procurement_type', body_text)
		detail_description = self._extract_description(body_text)

		detail_document_indicators = self._extract_text_indicators(
			body_text,
			markers=_DOCUMENT_TEXT_MARKERS,
		)
		detail_public_action_indicators = self._extract_text_indicators(
			body_text,
			markers=_PUBLIC_ACTION_MARKERS,
		)

		stronger_fields = self._build_stronger_fields(
			table_item=table_item,
			detail_title=detail_title,
			detail_issuing_entity=detail_issuing_entity,
			detail_tender_ref=detail_tender_ref,
			detail_closing_date_raw=detail_closing_date_raw,
			detail_opening_date_raw=detail_opening_date_raw,
			detail_published_at_raw=detail_published_at_raw,
			detail_category=detail_category,
			detail_procurement_type=detail_procurement_type,
			detail_description=detail_description,
		)

		return SaudiMisaDetailItem(
			item_index=table_item.item_index,
			extracted_at=datetime.now(UTC),
			table_title_text=table_item.title_text,
			table_reference_number=table_item.visible_reference_number,
			table_inquiry_deadline_primary=table_item.visible_offering_date,
			table_inquiry_deadline_secondary=table_item.visible_bid_deadline,
			table_offer_opening_primary=table_item.visible_inquiry_deadline,
			table_offer_opening_secondary=table_item.visible_bid_deadline,
			table_status_link_text=table_item.visible_status_link_text,
			detail_url=table_item.detail_url,
			final_url=final_url,
			detail_page_title=detail_page_title,
			access_status='detail_page',
			detail_title=detail_title,
			detail_issuing_entity=detail_issuing_entity,
			detail_tender_ref=detail_tender_ref,
			detail_closing_date_raw=detail_closing_date_raw,
			detail_published_at_raw=detail_published_at_raw,
			detail_opening_date_raw=detail_opening_date_raw,
			detail_category=detail_category,
			detail_procurement_type=detail_procurement_type,
			detail_description=detail_description,
			detail_document_indicators=detail_document_indicators,
			detail_public_action_indicators=detail_public_action_indicators,
			stronger_fields=stronger_fields,
			raw_text=raw_text,
		)

	async def _get_body_text(self, page: Page) -> str:
		"""Extract full body text for blocker detection and inspection."""
		body_locator = page.locator('body')
		if await body_locator.count() == 0:
			raise SaudiMisaDetailNavigationError('detail page body selector was not found')
		return await body_locator.inner_text()

	def _is_blocked_page(self, detail_page_title: str, raw_text: str) -> bool:
		"""Return whether the detail page is challenge-gated or blocked."""
		normalized_title = detail_page_title.casefold()
		normalized_body = raw_text.casefold()
		if 'please enable javascript' in normalized_title:
			return True
		return any(marker in normalized_body for marker in _BLOCKED_TEXT_MARKERS)

	async def _sleep_with_jitter(self) -> None:
		"""Wait a bounded randomized interval after navigation."""
		await asyncio.sleep(random.uniform(self.MIN_JITTER_MS / 1000, self.MAX_JITTER_MS / 1000))

	def _build_stronger_fields(
		self,
		*,
		table_item: SaudiMisaRawItem,
		detail_title: str | None,
		detail_issuing_entity: str | None,
		detail_tender_ref: str | None,
		detail_closing_date_raw: str | None,
		detail_opening_date_raw: str | None,
		detail_published_at_raw: str | None,
		detail_category: str | None,
		detail_procurement_type: str | None,
		detail_description: str | None,
	) -> tuple[str, ...]:
		"""Report which fields became stronger on the detail page versus the MISA table."""
		stronger_fields: list[str] = []

		if detail_title and detail_title != table_item.title_text:
			stronger_fields.append('detail_title')
		if detail_issuing_entity:
			stronger_fields.append('issuing_entity')
		if detail_tender_ref and detail_tender_ref != table_item.visible_reference_number:
			stronger_fields.append('tender_ref')
		if detail_closing_date_raw:
			stronger_fields.append('closing_date')
		if detail_opening_date_raw or detail_published_at_raw:
			stronger_fields.append('opening_or_published_date')
		if detail_category or detail_procurement_type:
			stronger_fields.append('category_or_procurement_type')
		if detail_description:
			stronger_fields.append('description')

		return tuple(stronger_fields)

	def _extract_labeled_value(self, field_name: str, body_text: str) -> str | None:
		"""Extract one labeled value from the normalized detail-page text."""
		pattern = _LABEL_VALUE_PATTERNS[field_name]
		match = pattern.search(body_text)
		if match is None:
			return None
		return self._none_if_empty(match.group(1))

	def _extract_classification(self, body_text: str) -> str | None:
		"""Extract visible classification labels from the detail page when present."""
		match = _CLASSIFICATION_BLOCK_RE.search(body_text)
		if match is None:
			return None

		raw_block = match.group('value')
		values: list[str] = []
		seen: set[str] = set()
		for raw_line in raw_block.splitlines():
			line = self._normalize_whitespace(raw_line)
			if not line:
				continue
			bullet_match = _CLASSIFICATION_BULLET_RE.fullmatch(line)
			candidate = line if bullet_match is None else self._normalize_whitespace(bullet_match.group(1))
			candidate = self._none_if_empty(candidate)
			if candidate is None or candidate in {'|', ':'}:
				continue
			if candidate in seen:
				continue
			seen.add(candidate)
			values.append(candidate)

		if not values:
			return None
		return ' / '.join(values)

	def _extract_description(self, body_text: str) -> str | None:
		"""Extract the visible competition purpose line when present."""
		match = re.search(r'الغاية\s+من\s+المنافسة\s*[:：]?\s*([^\n]+)', body_text)
		if match is None:
			return None
		return self._none_if_empty(match.group(1))

	def _extract_text_indicators(
		self,
		text: str,
		*,
		markers: tuple[str, ...],
	) -> tuple[str, ...]:
		"""Return ordered visible markers found in the text."""
		normalized_text = text.casefold()
		return tuple(marker for marker in markers if marker.casefold() in normalized_text)

	@staticmethod
	def _normalize_whitespace(value: str) -> str:
		"""Collapse whitespace while preserving visible content order."""
		return '\n'.join(
			_WHITESPACE_RE.sub(' ', line.replace('\xa0', ' ')).strip()
			for line in value.splitlines()
			if _WHITESPACE_RE.sub(' ', line.replace('\xa0', ' ')).strip()
		)

	@staticmethod
	def _none_if_empty(value: str | None) -> str | None:
		"""Convert blank strings to None."""
		if value is None:
			return None
		cleaned = value.strip()
		return cleaned or None


async def run_saudi_misa_detail_crawl(
	*,
	sample_size: int | None = 5,
	dashboard_items: Sequence[SaudiMisaRawItem] | None = None,
) -> SaudiMisaDetailCrawlResult:
	"""Convenience entrypoint for one Saudi MISA-linked detail crawl."""
	crawler = SaudiMisaDetailCrawler(
		sample_size=sample_size,
		dashboard_items=dashboard_items,
	)
	return await crawler.crawl()
