from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import parse_qsl, urljoin, urlparse

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from src.crawler.sources.saudi_etimad_config import SAUDI_ETIMAD_CONFIG

_WHITESPACE_RE = re.compile(r'\s+')
_REFERENCE_LINE_RE = re.compile(
	r'(?:^|\n)[^\n]*(?:الرقم المرجعي للمنافسة|الرقم المرجعي|reference)[^\n]*',
	re.IGNORECASE,
)
_DATE_LINE_RE = re.compile(
	r'(?:^|\n)[^\n]*(?:تاريخ|آخر موعد|موعد|date|closing)[^\n]*',
	re.IGNORECASE,
)
_PUBLICATION_DATE_RE = re.compile(r'تاريخ\s+النشر\s*[:：]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})')
_SUPPORT_ID_RE = re.compile(r'(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)', re.IGNORECASE)
_TITLE_REFERENCE_RE = re.compile(r'\b([0-9]{6,})\b')


class SaudiEtimadCrawlerError(RuntimeError):
	"""Base class for Saudi Etimad crawler failures."""


class SaudiEtimadNavigationError(SaudiEtimadCrawlerError):
	"""Raised when the listing page cannot be loaded or verified."""


class SaudiEtimadBlockedError(SaudiEtimadCrawlerError):
	"""Raised when the public page is blocked by anti-bot or access controls."""


class SaudiEtimadExtractionError(SaudiEtimadCrawlerError):
	"""Raised when deterministic extraction cannot proceed."""


@dataclass(frozen=True)
class SaudiEtimadRawItem:
	"""
	Raw deterministic listing item extracted from the Saudi Etimad public page.

	Notes:
	    - This is intentionally source-specific and unnormalized.
	    - It is only for proving deterministic public-source access and shape.
	"""

	item_index: int
	extracted_at: datetime
	page_url: str
	title_text: str
	issuing_entity: str | None
	publication_date: str | None
	procurement_type_label: str | None
	visible_reference: str | None
	visible_closing_date_raw: str | None
	visible_opening_date_raw: str | None
	detail_url: str
	raw_text: str
	reference_fields: tuple[str, ...]
	date_fields: tuple[str, ...]


@dataclass(frozen=True)
class SaudiEtimadCrawlResult:
	"""Structured result for one Saudi Etimad public listing-page crawl."""

	source_name: str
	listing_url: str
	final_url: str
	page_title: str
	extracted_at: datetime
	total_items: int
	items: tuple[SaudiEtimadRawItem, ...]


class SaudiEtimadCrawler:
	"""
	Deterministic crawler for the Saudi Etimad public competitions listing.

	Scope:
	    - navigate to the public listing page
	    - verify the page is the expected source and not an anti-bot wall
	    - extract raw listing artifacts from visible detail links
	    - return only source-specific raw content

	Non-goals:
	    - no AI extraction
	    - no database writes
	    - no normalization or ingestion
	    - no pagination or detail-page crawling yet
	"""

	USER_AGENT: Final[str] = (
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
	)

	def __init__(self) -> None:
		self._config = SAUDI_ETIMAD_CONFIG

	async def crawl(self) -> SaudiEtimadCrawlResult:
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

					return SaudiEtimadCrawlResult(
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
			locale='ar-SA',
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
			raise SaudiEtimadNavigationError(f"failed to navigate to '{self._config.listing_url}'") from exc

		if response is None:
			raise SaudiEtimadNavigationError('navigation returned no HTTP response')

		if response.status >= 400:
			raise SaudiEtimadNavigationError(f'navigation failed with HTTP status {response.status}')

		await self._sleep_with_jitter()

	async def _get_body_text(self, page: Page) -> str:
		"""Extract full body text for verification and blocker detection."""
		body_locator = page.locator(self._config.page_body)
		if await body_locator.count() == 0:
			raise SaudiEtimadNavigationError('page body selector was not found')
		return await body_locator.inner_text()

	def _ensure_not_blocked(self, body_text: str) -> None:
		"""Raise an explicit error if the page appears blocked or challenged."""
		normalized_body = body_text.casefold()
		matched_markers = [marker for marker in self._config.anti_bot_text_markers if marker in normalized_body]
		if not matched_markers:
			return

		support_match = _SUPPORT_ID_RE.search(body_text)
		support_suffix = ''
		if support_match:
			support_suffix = f' ({support_match.group(1)}={support_match.group(2)})'

		raise SaudiEtimadBlockedError(
			f'anti-bot or access-control page detected{support_suffix}; matched markers={matched_markers}'
		)

	def _verify_page(self, body_text: str) -> None:
		"""Verify that expected public listing markers are present."""
		normalized_body = body_text.casefold()
		matched_markers = [marker for marker in self._config.expected_page_text_markers if marker.casefold() in normalized_body]

		if not matched_markers:
			raise SaudiEtimadNavigationError('page verification failed; expected Saudi Etimad listing markers were not found')

	async def _extract_items(self, page: Page) -> list[SaudiEtimadRawItem]:
		"""Extract raw item containers from visible detail links."""
		link_locator = page.locator(self._config.detail_links)
		link_count = await link_locator.count()

		if link_count == 0:
			raise SaudiEtimadExtractionError('no detail links were found for extraction')

		extracted_at = datetime.now(UTC)
		items: list[SaudiEtimadRawItem] = []
		seen_hrefs: set[str] = set()

		for item_index in range(link_count):
			link = link_locator.nth(item_index)
			href = await link.get_attribute('href')
			if not isinstance(href, str) or not href.strip():
				continue

			detail_url = self._validate_detail_url(
				urljoin(
					page.url,
					self._normalize_href(href),
				)
			)
			if detail_url in seen_hrefs:
				continue

			raw_text = await self._extract_link_container_text(link)
			normalized_raw_text = self._normalize_whitespace(raw_text)
			if not normalized_raw_text:
				continue

			raw_lines = [
				self._normalize_whitespace(line) for line in normalized_raw_text.splitlines() if self._normalize_whitespace(line)
			]

			title_text = self._derive_title(
				anchor_text=self._normalize_whitespace(await link.inner_text()),
				raw_lines=raw_lines,
			)
			publication_date = self._extract_publication_date(normalized_raw_text)
			procurement_type_label = self._extract_procurement_type_label(raw_lines)
			issuing_entity = self._extract_issuing_entity(raw_lines, title_text)
			visible_reference = self._extract_visible_reference(
				raw_text=normalized_raw_text,
				title_text=title_text,
			)
			visible_closing_date_raw = self._extract_labeled_listing_date(
				raw_text=normalized_raw_text,
				labels=('آخر موعد لتقديم العروض', 'اخر موعد لتقديم العروض'),
			)
			visible_opening_date_raw = self._extract_labeled_listing_date(
				raw_text=normalized_raw_text,
				labels=('تاريخ ووقت فتح العروض', 'تاريخ وقت فتح العروض'),
			)
			reference_fields = self._extract_pattern_lines(
				pattern=_REFERENCE_LINE_RE,
				raw_text=normalized_raw_text,
			)
			date_fields = self._extract_pattern_lines(
				pattern=_DATE_LINE_RE,
				raw_text=normalized_raw_text,
			)

			items.append(
				SaudiEtimadRawItem(
					item_index=len(items),
					extracted_at=extracted_at,
					page_url=page.url,
					title_text=title_text,
					issuing_entity=issuing_entity,
					publication_date=publication_date,
					procurement_type_label=procurement_type_label,
					visible_reference=visible_reference,
					visible_closing_date_raw=visible_closing_date_raw,
					visible_opening_date_raw=visible_opening_date_raw,
					detail_url=detail_url,
					raw_text=normalized_raw_text,
					reference_fields=reference_fields,
					date_fields=date_fields,
				)
			)
			seen_hrefs.add(detail_url)

		if not items:
			raise SaudiEtimadExtractionError('detail links were found, but no non-empty raw item content could be extracted')

		return items

	async def _extract_link_container_text(self, link_locator) -> str:
		"""Extract the closest useful ancestor text for a listing artifact."""
		text = await link_locator.evaluate(
			"""
            (element) => {
              const minLength = 60;
              let current = element;
              for (let depth = 0; depth < 6 && current; depth += 1) {
                const text = (current.innerText || "").trim();
                if (text.length >= minLength) {
                  return text;
                }
                current = current.parentElement;
              }
              return (element.innerText || "").trim();
            }
            """
		)
		return text if isinstance(text, str) else ''

	def _derive_title(self, anchor_text: str, raw_lines: list[str]) -> str:
		"""Derive a stable item title from anchor or raw listing text."""
		if anchor_text and anchor_text.casefold() not in self._config.generic_link_labels:
			return anchor_text

		for candidate in raw_lines:
			if not candidate:
				continue
			lowered = candidate.casefold()
			if lowered.startswith('تاريخ النشر'):
				continue
			if any(marker.casefold() in lowered for marker in self._config.expected_page_text_markers[1:]):
				continue
			if lowered in self._config.generic_link_labels:
				continue
			return candidate

		raise SaudiEtimadExtractionError('unable to derive a stable title from raw item text')

	def _extract_publication_date(self, raw_text: str) -> str | None:
		"""Extract the visible publication date when explicitly shown."""
		match = _PUBLICATION_DATE_RE.search(raw_text)
		if match is None:
			return None
		return match.group(1)

	def _extract_procurement_type_label(self, raw_lines: list[str]) -> str | None:
		"""Extract the visible procurement type label from line-oriented item text."""
		if len(raw_lines) < 2:
			return None

		if raw_lines[0].startswith('تاريخ النشر') and len(raw_lines) >= 3:
			candidate = raw_lines[1]
			if candidate not in self._config.generic_link_labels:
				return candidate

		return None

	def _extract_issuing_entity(self, raw_lines: list[str], title_text: str) -> str | None:
		"""Extract the visible issuing entity when it appears as its own line."""
		title_index = -1
		for index, line in enumerate(raw_lines):
			if line == title_text:
				title_index = index
				break
		if title_index == -1:
			return None

		for line in raw_lines[title_index + 1 :]:
			if line in self._config.generic_link_labels:
				continue
			if line.startswith('تاريخ النشر'):
				continue
			return line
		return None

	def _extract_visible_reference(self, *, raw_text: str, title_text: str) -> str | None:
		"""Extract a visible numeric reference only when explicitly present."""
		for line in self._extract_pattern_lines(pattern=_REFERENCE_LINE_RE, raw_text=raw_text):
			match = _TITLE_REFERENCE_RE.search(line)
			if match is not None:
				return match.group(1)

		title_match = _TITLE_REFERENCE_RE.search(title_text)
		if title_match is not None:
			return title_match.group(1)

		return None

	def _extract_pattern_lines(
		self,
		*,
		pattern: re.Pattern[str],
		raw_text: str,
	) -> tuple[str, ...]:
		"""Extract distinct labeled lines from raw text using a deterministic pattern."""
		values: list[str] = []
		seen: set[str] = set()
		for match in pattern.finditer(raw_text):
			value = self._normalize_whitespace(match.group(0))
			if not value or value in seen:
				continue
			values.append(value)
			seen.add(value)
		return tuple(values)

	def _extract_labeled_listing_date(
		self,
		*,
		raw_text: str,
		labels: tuple[str, ...],
	) -> str | None:
		"""Extract a visible listing date/time only when its label is explicitly present."""
		for raw_line in raw_text.splitlines():
			line = self._normalize_whitespace(raw_line)
			if not line:
				continue
			for label in labels:
				if label not in line:
					continue
				suffix = self._normalize_whitespace(line.split(label, maxsplit=1)[1])
				extracted_value = self._extract_date_value(suffix)
				if extracted_value is not None:
					return extracted_value
		return None

	def _extract_date_value(self, raw_value: str) -> str | None:
		"""Return the first supported visible date token from a listing label suffix."""
		match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', raw_value)
		if match is not None:
			return match.group(0)

		match = re.search(r'\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\b', raw_value)
		if match is not None:
			return match.group(0)

		match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', raw_value)
		if match is not None:
			return match.group(0)

		return None

	def _normalize_whitespace(self, value: str) -> str:
		"""Collapse repeated whitespace while keeping line boundaries stable."""
		collapsed_lines = [_WHITESPACE_RE.sub(' ', line).strip() for line in value.splitlines() if line.strip()]
		return '\n'.join(collapsed_lines)

	def _normalize_href(self, href: str) -> str:
		"""Remove incidental whitespace from href values before joining."""
		return ''.join(href.split())

	def _validate_detail_url(self, detail_url: str) -> str:
		"""Validate that the detail URL stays on the expected Etimad public route."""
		parsed = urlparse(detail_url)
		if parsed.scheme != 'https':
			raise SaudiEtimadExtractionError('detail URL is not https')
		if parsed.netloc != 'tenders.etimad.sa':
			raise SaudiEtimadExtractionError('detail URL does not stay on tenders.etimad.sa')
		if parsed.path != '/Tender/DetailsForVisitor':
			raise SaudiEtimadExtractionError('detail URL path is not the expected public detail route')

		query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
		if not any(key == 'STenderId' and value for key, value in query_pairs):
			raise SaudiEtimadExtractionError('detail URL is missing a non-empty STenderId query parameter')

		return detail_url

	async def _sleep_with_jitter(self) -> None:
		"""Apply bounded deterministic-friendly jitter between actions."""
		jitter_ms = random.randint(
			self._config.min_jitter_ms,
			self._config.max_jitter_ms,
		)
		await asyncio.sleep(jitter_ms / 1000)


async def run_saudi_etimad_crawl() -> SaudiEtimadCrawlResult:
	"""Convenience entrypoint for programmatic verification."""
	crawler = SaudiEtimadCrawler()
	return await crawler.crawl()
