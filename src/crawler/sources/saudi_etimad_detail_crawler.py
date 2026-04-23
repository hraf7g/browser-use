from __future__ import annotations

import asyncio
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.saudi_etimad_config import SAUDI_ETIMAD_CONFIG
from src.crawler.sources.saudi_etimad_crawler import SaudiEtimadRawItem, run_saudi_etimad_crawl

_WHITESPACE_RE = re.compile(r'\s+')
_LABEL_VALUE_PATTERNS: dict[str, re.Pattern[str]] = {
	'title': re.compile(r'اسم\s+المنافسة\s*[:：]?\s*([^\n]+)'),
	'competition_number': re.compile(r'رقم\s+المنافسة\s*[:：]?\s*([^\n]+)'),
	'reference_number': re.compile(r'الرقم\s+المرجعي\s*[:：]?\s*([^\n]+)'),
	'procurement_type': re.compile(r'نوع\s+المنافسة\s*[:：]?\s*([^\n]+)'),
	'issuing_entity': re.compile(r'الجهة\s+الحكومي(?:ه|ة)\s*[:：]?\s*([^\n]+)'),
	'remaining_time': re.compile(r'الوقت\s+المتبقى\s*[:：]?\s*([^\n]+)'),
}


class SaudiEtimadDetailCrawlerError(RuntimeError):
	"""Base class for Saudi Etimad detail-page crawl failures."""


class SaudiEtimadDetailNavigationError(SaudiEtimadDetailCrawlerError):
	"""Raised when a Saudi Etimad detail page cannot be loaded."""


class SaudiEtimadDetailAccessError(SaudiEtimadDetailCrawlerError):
	"""Raised when the Saudi Etimad detail page is blocked or inaccessible."""


class SaudiEtimadDetailExtractionError(SaudiEtimadDetailCrawlerError):
	"""Raised when deterministic detail-page extraction cannot proceed."""


@dataclass(frozen=True)
class SaudiEtimadDetailItem:
	"""One sampled Saudi Etimad detail page and the visible fields extracted from it."""

	item_index: int
	extracted_at: datetime
	dashboard_title_text: str
	dashboard_issuing_entity: str | None
	dashboard_publication_date: str | None
	dashboard_procurement_type_label: str | None
	dashboard_visible_reference: str | None
	dashboard_visible_closing_date_raw: str | None
	dashboard_visible_opening_date_raw: str | None
	detail_url: str
	final_url: str
	detail_page_title: str
	access_status: str
	detail_title: str | None
	detail_issuing_entity: str | None
	detail_competition_number: str | None
	detail_reference_number: str | None
	detail_procurement_type: str | None
	detail_remaining_time_raw: str | None
	stronger_fields: tuple[str, ...]
	raw_text: str


@dataclass(frozen=True)
class SaudiEtimadDetailCrawlResult:
	"""Structured summary of sampled Saudi Etimad detail-page inspection."""

	source_name: str
	listing_url: str
	final_listing_url: str
	sample_count: int
	successful_detail_pages: int
	extracted_at: datetime
	items: tuple[SaudiEtimadDetailItem, ...]


class SaudiEtimadDetailCrawler:
	"""Deterministic inspector for Saudi Etimad public detail pages."""

	USER_AGENT: Final[str] = (
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
	)

	def __init__(
		self,
		*,
		sample_size: int | None = 5,
		dashboard_items: Sequence[SaudiEtimadRawItem] | None = None,
	) -> None:
		self._config = SAUDI_ETIMAD_CONFIG
		self._sample_size = None if sample_size is None else max(1, sample_size)
		self._dashboard_items = None if dashboard_items is None else tuple(dashboard_items)

	async def crawl(self) -> SaudiEtimadDetailCrawlResult:
		"""Inspect live Saudi Etimad public detail URLs."""
		listing_result = await run_saudi_etimad_crawl()
		source_items = self._dashboard_items or listing_result.items
		sampled_items = source_items if self._sample_size is None else source_items[: self._sample_size]
		if not sampled_items:
			raise SaudiEtimadDetailExtractionError('listing crawl returned no sample rows for detail inspection')

		async with async_playwright() as playwright:
			browser = await playwright.chromium.launch(headless=True)
			try:
				context = await self._new_context(browser)
				try:
					items: list[SaudiEtimadDetailItem] = []
					for item in sampled_items:
						items.append(await self._inspect_detail_page(context, item))
				finally:
					await context.close()
			finally:
				await browser.close()

		successful_detail_pages = sum(1 for item in items if item.access_status == 'detail_page')
		return SaudiEtimadDetailCrawlResult(
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
			locale='ar-SA',
			timezone_id='Asia/Riyadh',
		)

	async def _inspect_detail_page(
		self,
		context: BrowserContext,
		dashboard_item: SaudiEtimadRawItem,
	) -> SaudiEtimadDetailItem:
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
				raise SaudiEtimadDetailNavigationError(
					f"failed to navigate to '{dashboard_item.detail_url}': {type(exc).__name__}: {exc}"
				) from exc

			if response is None:
				raise SaudiEtimadDetailNavigationError('detail navigation returned no HTTP response')
			if response.status >= 400:
				raise SaudiEtimadDetailNavigationError(f'detail navigation failed with HTTP status {response.status}')

			await self._sleep_with_jitter()
			detail_page_title = (await page.title()).strip()
			raw_text = await self._get_body_text(page)
			self._ensure_not_blocked(raw_text)
			self._verify_detail_page(raw_text)
			return self._extract_visible_detail_fields(
				dashboard_item=dashboard_item,
				detail_page_title=detail_page_title,
				final_url=page.url,
				raw_text=raw_text,
			)
		finally:
			await page.close()

	async def _get_body_text(self, page: Page) -> str:
		"""Extract normalized body text for visible field parsing."""
		body_locator = page.locator(self._config.page_body)
		if await body_locator.count() == 0:
			raise SaudiEtimadDetailExtractionError('detail page body selector was not found')
		return self._normalize_whitespace(await body_locator.inner_text())

	def _ensure_not_blocked(self, body_text: str) -> None:
		"""Raise an explicit error if the detail page appears blocked."""
		normalized_body = body_text.casefold()
		matched_markers = [marker for marker in self._config.anti_bot_text_markers if marker in normalized_body]
		if matched_markers:
			raise SaudiEtimadDetailAccessError(f'anti-bot or access-control page detected; matched markers={matched_markers}')

	def _verify_detail_page(self, body_text: str) -> None:
		"""Verify that the expected public detail-page markers are present."""
		normalized_body = body_text.casefold()
		required_markers = ('تفاصيل المنافسة', 'المعلومات الأساسية')
		if not all(marker.casefold() in normalized_body for marker in required_markers):
			raise SaudiEtimadDetailExtractionError(
				'detail page verification failed; expected Etimad detail markers were not found'
			)

	def _extract_visible_detail_fields(
		self,
		*,
		dashboard_item: SaudiEtimadRawItem,
		detail_page_title: str,
		final_url: str,
		raw_text: str,
	) -> SaudiEtimadDetailItem:
		"""Extract only clearly visible deterministic detail-page fields."""
		detail_title = self._extract_labeled_value('title', raw_text)
		detail_issuing_entity = self._extract_labeled_value('issuing_entity', raw_text)
		detail_competition_number = self._extract_labeled_value('competition_number', raw_text)
		detail_reference_number = self._extract_labeled_value('reference_number', raw_text)
		detail_procurement_type = self._extract_labeled_value('procurement_type', raw_text)
		detail_remaining_time_raw = self._extract_labeled_value('remaining_time', raw_text)
		stronger_fields = self._determine_stronger_fields(
			dashboard_item=dashboard_item,
			detail_title=detail_title,
			detail_issuing_entity=detail_issuing_entity,
			detail_competition_number=detail_competition_number,
			detail_reference_number=detail_reference_number,
			detail_procurement_type=detail_procurement_type,
		)

		return SaudiEtimadDetailItem(
			item_index=dashboard_item.item_index,
			extracted_at=datetime.now(UTC),
			dashboard_title_text=dashboard_item.title_text,
			dashboard_issuing_entity=dashboard_item.issuing_entity,
			dashboard_publication_date=dashboard_item.publication_date,
			dashboard_procurement_type_label=dashboard_item.procurement_type_label,
			dashboard_visible_reference=dashboard_item.visible_reference,
			dashboard_visible_closing_date_raw=dashboard_item.visible_closing_date_raw,
			dashboard_visible_opening_date_raw=dashboard_item.visible_opening_date_raw,
			detail_url=dashboard_item.detail_url,
			final_url=final_url,
			detail_page_title=detail_page_title,
			access_status='detail_page',
			detail_title=detail_title,
			detail_issuing_entity=detail_issuing_entity,
			detail_competition_number=detail_competition_number,
			detail_reference_number=detail_reference_number,
			detail_procurement_type=detail_procurement_type,
			detail_remaining_time_raw=detail_remaining_time_raw,
			stronger_fields=stronger_fields,
			raw_text=raw_text,
		)

	def _extract_labeled_value(self, field_name: str, raw_text: str) -> str | None:
		"""Extract one labeled value from normalized detail-page body text."""
		pattern = _LABEL_VALUE_PATTERNS[field_name]
		match = pattern.search(raw_text)
		if match is None:
			return None
		return self._none_if_empty(match.group(1))

	def _determine_stronger_fields(
		self,
		*,
		dashboard_item: SaudiEtimadRawItem,
		detail_title: str | None,
		detail_issuing_entity: str | None,
		detail_competition_number: str | None,
		detail_reference_number: str | None,
		detail_procurement_type: str | None,
	) -> tuple[str, ...]:
		"""Mark detail fields that are clearly stronger than the listing-row view."""
		stronger_fields: list[str] = []

		if self._is_stronger_text(detail_title, dashboard_item.title_text):
			stronger_fields.append('title')
		if self._is_stronger_text(detail_issuing_entity, dashboard_item.issuing_entity):
			stronger_fields.append('issuing_entity')
		if self._is_stronger_text(detail_procurement_type, dashboard_item.procurement_type_label):
			stronger_fields.append('category')

		detail_ref = self._preferred_text(detail_competition_number, detail_reference_number)
		if self._is_stronger_text(detail_ref, dashboard_item.visible_reference):
			stronger_fields.append('tender_ref')

		return tuple(stronger_fields)

	def _is_stronger_text(self, detail_value: str | None, dashboard_value: str | None) -> bool:
		"""Return whether the detail value is visibly stronger than the dashboard value."""
		detail_cleaned = self._none_if_empty(detail_value)
		if detail_cleaned is None:
			return False

		dashboard_cleaned = self._none_if_empty(dashboard_value)
		if dashboard_cleaned is None:
			return True

		return detail_cleaned != dashboard_cleaned and len(detail_cleaned) >= len(dashboard_cleaned)

	def _preferred_text(self, *values: str | None) -> str | None:
		"""Return the first non-empty stripped text value."""
		for value in values:
			cleaned = self._none_if_empty(value)
			if cleaned is not None:
				return cleaned
		return None

	def _normalize_whitespace(self, value: str) -> str:
		"""Collapse repeated whitespace while keeping line boundaries stable."""
		collapsed_lines = [_WHITESPACE_RE.sub(' ', line).strip() for line in value.splitlines() if line.strip()]
		return '\n'.join(collapsed_lines)

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


async def run_saudi_etimad_detail_crawl(
	*,
	sample_size: int | None = 5,
	dashboard_items: Sequence[SaudiEtimadRawItem] | None = None,
) -> SaudiEtimadDetailCrawlResult:
	"""Convenience entrypoint for programmatic Etimad detail-page verification."""
	crawler = SaudiEtimadDetailCrawler(
		sample_size=sample_size,
		dashboard_items=dashboard_items,
	)
	return await crawler.crawl()
