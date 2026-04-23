from __future__ import annotations

import asyncio
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.qatar_monaqasat_config import QATAR_MONAQASAT_CONFIG
from src.crawler.sources.qatar_monaqasat_crawler import (
	QatarMonaqasatRawItem,
	run_qatar_monaqasat_crawl,
)

_WHITESPACE_RE = re.compile(r'\s+')
_REFERENCE_RE = re.compile(r'\b\d{1,6}/\d{4}\b')
_DATE_VALUE_RE = re.compile(r'(?P<value>\d{2}/\d{2}/\d{4})')
_LABEL_VALUE_PATTERNS: dict[str, re.Pattern[str]] = {
	'tender_number': re.compile(r'tender number\s+([^\n]+)', re.IGNORECASE),
	'tender_type': re.compile(r'type\s+([^\n]+)', re.IGNORECASE),
	'subject': re.compile(r'subject\s+([^\n]+)', re.IGNORECASE),
	'ministry': re.compile(r'ministry\s+([^\n]+)', re.IGNORECASE),
	'entity_tender_number': re.compile(r"entity's tender number\s+([^\n]+)", re.IGNORECASE),
	'request_types': re.compile(r'request types\s+([^\n]+)', re.IGNORECASE),
	'publish_date': re.compile(r'publish date\s+([^\n]+)', re.IGNORECASE),
	'closing_date': re.compile(r'closing date\s+([^\n]+)', re.IGNORECASE),
	'opening_date': re.compile(
		r'(?:technical opening date|technical/financial opening date)\s+([^\n]+)',
		re.IGNORECASE,
	),
}


class QatarMonaqasatDetailCrawlerError(RuntimeError):
	"""Base class for Qatar Monaqasat detail-page crawl failures."""


class QatarMonaqasatDetailNavigationError(QatarMonaqasatDetailCrawlerError):
	"""Raised when a Qatar detail page cannot be loaded."""


class QatarMonaqasatDetailAccessError(QatarMonaqasatDetailCrawlerError):
	"""Raised when the Qatar detail page is not publicly accessible."""


class QatarMonaqasatDetailExtractionError(QatarMonaqasatDetailCrawlerError):
	"""Raised when deterministic detail-page extraction cannot proceed."""


@dataclass(frozen=True)
class QatarMonaqasatDetailItem:
	"""One sampled Qatar detail page and any deterministic fields visible on it."""

	item_index: int
	extracted_at: datetime
	dashboard_title_text: str
	dashboard_visible_reference: str | None
	dashboard_visible_publish_date: str | None
	dashboard_visible_ministry: str | None
	dashboard_visible_tender_type: str | None
	detail_url: str
	final_url: str
	detail_page_title: str
	access_status: str
	detail_title: str | None
	detail_ministry: str | None
	detail_tender_number: str | None
	detail_entity_tender_number: str | None
	detail_publish_date_raw: str | None
	detail_closing_date_raw: str | None
	detail_opening_date_raw: str | None
	detail_request_types: str | None
	detail_tender_type: str | None
	stronger_fields: tuple[str, ...]
	raw_text: str


@dataclass(frozen=True)
class QatarMonaqasatDetailCrawlResult:
	"""Structured summary of sampled Qatar detail-page inspection."""

	source_name: str
	listing_url: str
	final_listing_url: str
	sample_count: int
	successful_detail_pages: int
	extracted_at: datetime
	items: tuple[QatarMonaqasatDetailItem, ...]


class QatarMonaqasatDetailCrawler:
	"""
	Deterministic inspector for Qatar Monaqasat public detail pages.
	"""

	USER_AGENT: Final[str] = (
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
	)

	def __init__(
		self,
		*,
		sample_size: int | None = 5,
		dashboard_items: Sequence[QatarMonaqasatRawItem] | None = None,
	) -> None:
		self._config = QATAR_MONAQASAT_CONFIG
		self._sample_size = None if sample_size is None else max(1, sample_size)
		self._dashboard_items = None if dashboard_items is None else tuple(dashboard_items)

	async def crawl(self) -> QatarMonaqasatDetailCrawlResult:
		"""Inspect live Qatar public detail URLs."""
		listing_result = await run_qatar_monaqasat_crawl()
		source_items = self._dashboard_items or listing_result.items
		sampled_items = source_items if self._sample_size is None else source_items[: self._sample_size]
		if not sampled_items:
			raise QatarMonaqasatDetailExtractionError('listing crawl returned no sample rows for detail inspection')

		async with async_playwright() as playwright:
			browser = await playwright.chromium.launch(headless=True)
			try:
				context = await self._new_context(browser)
				try:
					items: list[QatarMonaqasatDetailItem] = []
					for item in sampled_items:
						items.append(await self._inspect_detail_page(context, item))
				finally:
					await context.close()
			finally:
				await browser.close()

		successful_detail_pages = sum(1 for item in items if item.access_status == 'detail_page')

		return QatarMonaqasatDetailCrawlResult(
			source_name=listing_result.source_name,
			listing_url=listing_result.listing_url,
			final_listing_url=listing_result.final_url,
			sample_count=len(items),
			successful_detail_pages=successful_detail_pages,
			extracted_at=datetime.now(UTC),
			items=tuple(items),
		)

	async def _new_context(self, browser: Browser) -> BrowserContext:
		"""Create a browser context consistent with the listing crawler."""
		return await browser.new_context(
			user_agent=self.USER_AGENT,
			viewport={'width': 1440, 'height': 1200},
			java_script_enabled=True,
			locale='en-QA',
			timezone_id='Asia/Qatar',
		)

	async def _inspect_detail_page(
		self,
		context: BrowserContext,
		dashboard_item: QatarMonaqasatRawItem,
	) -> QatarMonaqasatDetailItem:
		"""Open one detail URL and extract deterministic visible fields."""
		page = await context.new_page()
		try:
			try:
				response = await page.goto(
					dashboard_item.detail_url,
					wait_until='domcontentloaded',
					timeout=self._config.page_load_timeout_ms,
				)
			except Exception as exc:
				raise QatarMonaqasatDetailNavigationError(
					f"failed to navigate to '{dashboard_item.detail_url}': {type(exc).__name__}: {exc}"
				) from exc

			if response is None:
				raise QatarMonaqasatDetailNavigationError('detail navigation returned no HTTP response')
			if response.status >= 400:
				raise QatarMonaqasatDetailNavigationError(f'detail navigation failed with HTTP status {response.status}')

			await self._sleep_with_jitter()
			detail_page_title = (await page.title()).strip()
			raw_text = await self._get_body_text(page)
			self._ensure_not_blocked(raw_text)

			detail_item = self._extract_visible_detail_fields(
				dashboard_item=dashboard_item,
				detail_page_title=detail_page_title,
				final_url=page.url,
				raw_text=raw_text,
			)
			return detail_item
		finally:
			await page.close()

	async def _get_body_text(self, page: Page) -> str:
		"""Extract normalized body text for visible field parsing."""
		body_locator = page.locator(self._config.page_body)
		if await body_locator.count() == 0:
			raise QatarMonaqasatDetailExtractionError('detail page body selector was not found')
		return self._normalize_whitespace(await body_locator.inner_text())

	def _ensure_not_blocked(self, body_text: str) -> None:
		"""Raise an explicit error if the detail page appears blocked."""
		normalized_body = body_text.casefold()
		matched_markers = [marker for marker in self._config.anti_bot_text_markers if marker in normalized_body]
		if matched_markers:
			raise QatarMonaqasatDetailAccessError(f'anti-bot or access-control page detected; matched markers={matched_markers}')
		if 'tender announcement' not in normalized_body:
			raise QatarMonaqasatDetailExtractionError('detail page verification failed; expected Tender Announcement marker')

	def _extract_visible_detail_fields(
		self,
		*,
		dashboard_item: QatarMonaqasatRawItem,
		detail_page_title: str,
		final_url: str,
		raw_text: str,
	) -> QatarMonaqasatDetailItem:
		"""Extract only clearly visible deterministic detail-page fields."""
		detail_title = self._extract_labeled_value('subject', raw_text)
		detail_ministry = self._extract_labeled_value('ministry', raw_text)
		detail_tender_number = self._extract_labeled_value('tender_number', raw_text) or self._extract_reference(raw_text)
		detail_entity_tender_number = self._extract_labeled_value('entity_tender_number', raw_text)
		detail_publish_date_raw = self._extract_labeled_date('publish_date', raw_text)
		detail_closing_date_raw = self._extract_labeled_date('closing_date', raw_text)
		detail_opening_date_raw = self._extract_labeled_date('opening_date', raw_text)
		detail_request_types = self._extract_labeled_value('request_types', raw_text)
		detail_tender_type = self._extract_labeled_value('tender_type', raw_text)
		stronger_fields = self._determine_stronger_fields(
			dashboard_item=dashboard_item,
			detail_title=detail_title,
			detail_ministry=detail_ministry,
			detail_publish_date_raw=detail_publish_date_raw,
			detail_closing_date_raw=detail_closing_date_raw,
			detail_opening_date_raw=detail_opening_date_raw,
			detail_tender_type=detail_tender_type,
		)

		return QatarMonaqasatDetailItem(
			item_index=dashboard_item.item_index,
			extracted_at=datetime.now(UTC),
			dashboard_title_text=dashboard_item.title_text,
			dashboard_visible_reference=dashboard_item.visible_reference,
			dashboard_visible_publish_date=dashboard_item.visible_publish_date,
			dashboard_visible_ministry=dashboard_item.visible_ministry,
			dashboard_visible_tender_type=dashboard_item.visible_tender_type,
			detail_url=dashboard_item.detail_url,
			final_url=final_url,
			detail_page_title=detail_page_title,
			access_status='detail_page',
			detail_title=detail_title,
			detail_ministry=detail_ministry,
			detail_tender_number=detail_tender_number,
			detail_entity_tender_number=detail_entity_tender_number,
			detail_publish_date_raw=detail_publish_date_raw,
			detail_closing_date_raw=detail_closing_date_raw,
			detail_opening_date_raw=detail_opening_date_raw,
			detail_request_types=detail_request_types,
			detail_tender_type=detail_tender_type,
			stronger_fields=stronger_fields,
			raw_text=raw_text,
		)

	def _extract_reference(self, raw_text: str) -> str | None:
		"""Extract a visible tender number when explicitly shown."""
		match = _REFERENCE_RE.search(raw_text)
		if match is None:
			return None
		return match.group(0)

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
		match = pattern.search(raw_text)
		if match is None:
			return None
		return self._normalize_whitespace(match.group(1))

	def _determine_stronger_fields(
		self,
		*,
		dashboard_item: QatarMonaqasatRawItem,
		detail_title: str | None,
		detail_ministry: str | None,
		detail_publish_date_raw: str | None,
		detail_closing_date_raw: str | None,
		detail_opening_date_raw: str | None,
		detail_tender_type: str | None,
	) -> tuple[str, ...]:
		"""Identify which fields became stronger on the detail page than on the listing."""
		stronger_fields: list[str] = []

		if detail_title is not None and detail_title != dashboard_item.title_text:
			stronger_fields.append('title')
		if detail_ministry is not None and detail_ministry != dashboard_item.visible_ministry:
			stronger_fields.append('issuing_entity')
		if detail_publish_date_raw is not None:
			stronger_fields.append('published_at')
		if detail_closing_date_raw is not None:
			stronger_fields.append('closing_date')
		if detail_opening_date_raw is not None:
			stronger_fields.append('opening_date')
		if detail_tender_type is not None and detail_tender_type != dashboard_item.visible_tender_type:
			stronger_fields.append('category')

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


async def run_qatar_monaqasat_detail_crawl(
	*,
	sample_size: int | None = 5,
	dashboard_items: Sequence[QatarMonaqasatRawItem] | None = None,
) -> QatarMonaqasatDetailCrawlResult:
	"""Convenience entrypoint for live Qatar detail-page inspection."""
	crawler = QatarMonaqasatDetailCrawler(
		sample_size=sample_size,
		dashboard_items=dashboard_items,
	)
	return await crawler.crawl()
