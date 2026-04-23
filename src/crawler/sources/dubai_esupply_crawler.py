from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.dubai_esupply_config import DUBAI_ESUPPLY_CONFIG


class DubaiESupplyCrawlerError(RuntimeError):
	"""Base class for Dubai eSupply crawler failures."""


class DubaiESupplyNavigationError(DubaiESupplyCrawlerError):
	"""Raised when the listing page cannot be loaded or verified."""


class DubaiESupplyExtractionError(DubaiESupplyCrawlerError):
	"""Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class DubaiESupplyListingRow:
	"""
	Raw deterministic row extracted from the Dubai eSupply listing page.

	Notes:
	    - This is intentionally raw and source-specific.
	    - Mapping into normalized tender ingestion payloads will happen later.
	    - No heuristic field guessing is allowed here.
	"""

	row_index: int
	extracted_at: datetime
	page_url: str
	action_href: str | None
	cells: tuple[str, ...]
	row_text: str


@dataclass(frozen=True)
class DubaiESupplyCrawlResult:
	"""Structured result for one Dubai eSupply listing-page crawl."""

	source_name: str
	listing_url: str
	page_title: str
	extracted_at: datetime
	total_rows: int
	rows: tuple[DubaiESupplyListingRow, ...]


class DubaiESupplyCrawler:
	"""
	Deterministic crawler for the Dubai eSupply listing page.

	Scope:
	    - navigate to the configured listing page
	    - wait for the page to stabilize
	    - verify expected text markers exist
	    - extract raw table rows and cells
	    - return raw structured rows for later normalization

	Non-goals:
	    - no AI extraction
	    - no ingestion/database writes
	    - no field guessing from unverified table layouts
	    - no pagination yet
	"""

	USER_AGENT: Final[str] = (
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
	)

	def __init__(self) -> None:
		self._config = DUBAI_ESUPPLY_CONFIG

	async def crawl(self) -> DubaiESupplyCrawlResult:
		"""Run the listing-page crawl and return deterministic raw rows."""
		async with async_playwright() as playwright:
			browser = await playwright.chromium.launch(headless=True)
			try:
				context = await self._new_context(browser)
				try:
					page = await context.new_page()
					await self._navigate(page)
					await self._verify_page(page)
					rows = await self._extract_rows(page)
					page_title = await page.title()
					extracted_at = datetime.now(UTC)
					return DubaiESupplyCrawlResult(
						source_name=self._config.source_name,
						listing_url=page.url,
						page_title=page_title.strip(),
						extracted_at=extracted_at,
						total_rows=len(rows),
						rows=tuple(rows),
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
			timezone_id='Asia/Dubai',
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
			raise DubaiESupplyNavigationError(f"failed to navigate to '{self._config.listing_url}'") from exc

		if response is None:
			raise DubaiESupplyNavigationError('navigation returned no HTTP response')

		if response.status >= 400:
			raise DubaiESupplyNavigationError(f'navigation failed with HTTP status {response.status}')

		await self._sleep_with_jitter()

	async def _verify_page(self, page: Page) -> None:
		"""Verify that the page body contains expected text markers."""
		body_locator = page.locator(self._config.page_body)
		if await body_locator.count() == 0:
			raise DubaiESupplyNavigationError('page body selector was not found')

		body_text = await body_locator.inner_text()
		normalized_body = body_text.casefold()

		matched_markers = [marker for marker in self._config.expected_page_text_markers if marker.casefold() in normalized_body]

		if not matched_markers:
			raise DubaiESupplyNavigationError('page verification failed; expected text markers were not found')

		table_locator = page.locator(self._config.opportunities_table)
		if await table_locator.count() == 0:
			raise DubaiESupplyExtractionError('opportunities table selector was not found')

	async def _extract_rows(self, page: Page) -> list[DubaiESupplyListingRow]:
		"""Extract raw row/cell content from the listing table."""
		row_locator = page.locator(self._config.table_rows)
		row_count = await row_locator.count()

		if row_count == 0:
			raise DubaiESupplyExtractionError('no table rows were found for extraction')

		extracted_at = datetime.now(UTC)
		extracted_rows: list[DubaiESupplyListingRow] = []

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

			action_href = None
			action_link = row.locator('a').first
			if await action_link.count() > 0:
				href = await action_link.get_attribute('href')
				if isinstance(href, str) and href.strip():
					action_href = href.strip()

			extracted_rows.append(
				DubaiESupplyListingRow(
					row_index=row_index,
					extracted_at=extracted_at,
					page_url=page.url,
					action_href=action_href,
					cells=tuple(cells),
					row_text=row_text,
				)
			)

		if not extracted_rows:
			raise DubaiESupplyExtractionError('table rows were found, but no non-empty row content could be extracted')

		return extracted_rows

	async def _sleep_with_jitter(self) -> None:
		"""Apply bounded deterministic-friendly jitter between actions."""
		jitter_ms = random.randint(
			self._config.min_jitter_ms,
			self._config.max_jitter_ms,
		)
		await asyncio.sleep(jitter_ms / 1000)


async def run_dubai_esupply_crawl() -> DubaiESupplyCrawlResult:
	"""Convenience entrypoint for one Dubai eSupply crawl."""
	crawler = DubaiESupplyCrawler()
	return await crawler.crawl()
