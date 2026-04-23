from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from urllib.parse import urlparse

import httpx

from src.crawler.sources.saudi_moh_config import SAUDI_MOH_CONFIG

_WHITESPACE_RE = re.compile(r'\s+')
_HTML_TITLE_RE = re.compile(r'<title[^>]*>(.*?)</title>', re.IGNORECASE | re.DOTALL)
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_SCRIPT_JSON_RE = re.compile(
    r'<script[^>]*type=["\']application/(?:ld\+)?json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
_URL_RE = re.compile(r'https?://[^\s"\'<>]+', re.IGNORECASE)
_SUPPORT_ID_RE = re.compile(
    r'(support id|reference id)\s*[:#-]?\s*([A-Za-z0-9-]+)',
    re.IGNORECASE,
)


class SaudiMohStaticProbeError(RuntimeError):
    """Base class for Saudi MOH static-probe failures."""


class SaudiMohStaticFetchError(SaudiMohStaticProbeError):
    """Raised when the plain HTTP fetch cannot complete."""


@dataclass(frozen=True)
class SaudiMohStaticProbeItem:
    """One statically visible tender-like artifact extracted from HTML."""

    item_index: int
    title_text: str
    href: str | None
    visible_tender_number: str | None
    visible_tendering_date: str | None
    visible_bidding_deadline: str | None
    visible_opening_date: str | None
    visible_status: str | None


@dataclass(frozen=True)
class SaudiMohStaticProbeResult:
    """Structured static-feasibility result for the official Saudi MOH page."""

    source_name: str
    listing_url: str
    final_url: str
    fetched_at: datetime
    fetch_status: str
    status_code: int | None
    content_type: str | None
    page_title: str | None
    html_returned: bool
    redirected: bool
    blocked: bool
    empty: bool
    js_shell_only: bool
    tender_list_data_present: bool
    embedded_json_present: bool
    visible_api_endpoints_present: bool
    feasible_static_scraping: bool
    blocker_reason: str | None
    tender_link_count: int
    embedded_json_count: int
    visible_api_endpoint_count: int
    items: tuple[SaudiMohStaticProbeItem, ...]


class SaudiMohStaticProbe:
    """
    Plain-HTTP feasibility probe for the official Saudi MOH tenders page.

    Scope:
        - fetch the official MOH tenders page without browser automation
        - classify the returned content deterministically
        - inspect raw HTML for visible structured tender data, JSON, and API hints
        - report whether static scraping is feasible from this environment
    """

    USER_AGENT: Final[str] = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
    REQUEST_TIMEOUT_SECONDS: Final[float] = 45.0

    def __init__(self) -> None:
        self._config = SAUDI_MOH_CONFIG

    def probe(self) -> SaudiMohStaticProbeResult:
        """Run the plain-HTTP feasibility probe."""
        try:
            with httpx.Client(
                follow_redirects=True,
                timeout=self.REQUEST_TIMEOUT_SECONDS,
                headers={'User-Agent': self.USER_AGENT},
            ) as client:
                response = client.get(self._config.listing_url)
        except httpx.HTTPError as exc:
            raise SaudiMohStaticFetchError(
                f"plain HTTP fetch failed for '{self._config.listing_url}': "
                f'{type(exc).__name__}: {exc}'
            ) from exc

        html = response.text
        fetched_at = datetime.now(UTC)
        content_type = response.headers.get('content-type')
        final_url = str(response.url)
        page_title = self._extract_html_title(html)
        normalized_html = self._normalize_whitespace(html)
        lower_html = html.casefold()

        html_returned = 'html' in (content_type or '').casefold() and bool(html.strip())
        redirected = final_url != self._config.listing_url
        blocked, blocker_reason = self._classify_blocked(html)
        empty = html_returned and len(normalized_html) == 0
        js_shell_only = html_returned and self._is_js_shell_only(html)

        tender_links = self._extract_tender_links(html)
        items = self._extract_visible_items(normalized_html)
        embedded_json_count = self._count_embedded_json_blocks(html)
        visible_api_endpoint_count = self._count_visible_api_endpoints(html)

        tender_list_data_present = bool(items or tender_links or self._contains_tender_markers(html))
        embedded_json_present = embedded_json_count > 0
        visible_api_endpoints_present = visible_api_endpoint_count > 0

        if blocked:
            fetch_status = 'blocked'
        elif not html_returned:
            fetch_status = 'empty'
        elif js_shell_only:
            fetch_status = 'js_shell_only'
        elif redirected:
            fetch_status = 'redirected'
        else:
            fetch_status = 'reachable'

        feasible_static_scraping = (
            html_returned
            and not blocked
            and not empty
            and tender_list_data_present
        )

        return SaudiMohStaticProbeResult(
            source_name=self._config.source_name,
            listing_url=self._config.listing_url,
            final_url=final_url,
            fetched_at=fetched_at,
            fetch_status=fetch_status,
            status_code=response.status_code,
            content_type=content_type,
            page_title=page_title,
            html_returned=html_returned,
            redirected=redirected,
            blocked=blocked,
            empty=empty,
            js_shell_only=js_shell_only,
            tender_list_data_present=tender_list_data_present,
            embedded_json_present=embedded_json_present,
            visible_api_endpoints_present=visible_api_endpoints_present,
            feasible_static_scraping=feasible_static_scraping,
            blocker_reason=blocker_reason,
            tender_link_count=len(tender_links),
            embedded_json_count=embedded_json_count,
            visible_api_endpoint_count=visible_api_endpoint_count,
            items=tuple(items[:5]),
        )

    def _classify_blocked(self, html: str) -> tuple[bool, str | None]:
        """Detect obvious blocker/challenge content in returned HTML."""
        normalized_html = html.casefold()
        matched_markers = [
            marker
            for marker in self._config.anti_bot_text_markers
            if marker in normalized_html
        ]
        if not matched_markers:
            return False, None

        support_match = _SUPPORT_ID_RE.search(html)
        if support_match:
            return (
                True,
                f"{matched_markers[0]} ({support_match.group(1)}={support_match.group(2)})",
            )
        return True, matched_markers[0]

    def _is_js_shell_only(self, html: str) -> bool:
        """Classify HTML that contains almost no tender body content."""
        normalized = self._normalize_whitespace(self._strip_tags(html))
        if not normalized:
            return True
        if 'It looks like your browser does not have JavaScript enabled.' in normalized:
            return True
        if 'Please enable scripts and reload this page.' in normalized and not self._contains_tender_markers(html):
            return True
        return False

    def _extract_tender_links(self, html: str) -> list[str]:
        """Collect visible hrefs that point to tender/procurement-related pages."""
        links: list[str] = []
        seen: set[str] = set()
        for href in _HREF_RE.findall(html):
            cleaned = href.strip()
            lower = cleaned.casefold()
            if not cleaned or cleaned in seen:
                continue
            if any(
                marker in lower
                for marker in (
                    'etimad',
                    'monafasat',
                    'tender',
                    'procurement',
                    'purchas',
                )
            ):
                links.append(cleaned)
                seen.add(cleaned)
        return links

    def _count_embedded_json_blocks(self, html: str) -> int:
        """Count syntactically valid JSON script blocks visible in HTML."""
        count = 0
        for block in _SCRIPT_JSON_RE.findall(html):
            payload = block.strip()
            if not payload:
                continue
            try:
                json.loads(payload)
            except json.JSONDecodeError:
                continue
            count += 1
        return count

    def _count_visible_api_endpoints(self, html: str) -> int:
        """Count visible API/XHR-style endpoints present in raw HTML."""
        count = 0
        for candidate in _URL_RE.findall(html):
            parsed = urlparse(candidate.rstrip('.,);'))
            path = parsed.path.casefold()
            if any(token in path for token in ('/api/', '/_api/', 'ashx', 'service', 'rest')):
                count += 1
        return count

    def _extract_visible_items(self, normalized_html: str) -> list[SaudiMohStaticProbeItem]:
        """Recover a small deterministic sample of visible tender rows from HTML text."""
        marker = 'Planned Tenders and procurement:'
        boundary = 'Archived Tenders and Procurement (Closed):'
        if marker not in normalized_html or boundary not in normalized_html:
            return []

        section = normalized_html.split(marker, 1)[1].split(boundary, 1)[0]
        lines = [line.strip() for line in section.split('  ') if line.strip()]
        compact = ' '.join(lines)

        item_matches = re.finditer(
            r'(?P<index>\d+)\s+(?P<title>.+?)\s+'
            r'(?P<tender_type>(?:Consulting|Technical|Engineering|Supply|General)[^0-9]+?)\s+'
            r'(?P<offer_type>(?:Limited|Direct|Government)[^0-9]+?)\s+'
            r'(?P<duration>\d+\s+Days?)\s+'
            r'(?P<tendering_date>[A-Z][a-z]+\s?\d{1,2},\s\d{4})',
            compact,
        )

        items: list[SaudiMohStaticProbeItem] = []
        for item_index, match in enumerate(item_matches):
            items.append(
                SaudiMohStaticProbeItem(
                    item_index=item_index,
                    title_text=self._normalize_whitespace(match.group('title')),
                    href=None,
                    visible_tender_number=None,
                    visible_tendering_date=self._normalize_whitespace(
                        match.group('tendering_date')
                    ),
                    visible_bidding_deadline=None,
                    visible_opening_date=None,
                    visible_status=self._normalize_whitespace(match.group('offer_type')),
                )
            )
            if len(items) == 5:
                break
        return items

    def _contains_tender_markers(self, html: str) -> bool:
        """Check whether static HTML visibly contains tender-structured markers."""
        normalized = self._normalize_whitespace(self._strip_tags(html))
        return all(
            marker in normalized
            for marker in (
                'Tenders and Procurement',
                'Tender Title',
                'Expected launch Date',
            )
        )

    @staticmethod
    def _extract_html_title(html: str) -> str | None:
        """Extract the HTML title if present."""
        match = _HTML_TITLE_RE.search(html)
        if match is None:
            return None
        return SaudiMohStaticProbe._normalize_whitespace(
            SaudiMohStaticProbe._strip_tags(match.group(1))
        ) or None

    @staticmethod
    def _strip_tags(value: str) -> str:
        """Remove raw HTML tags for text-only inspection."""
        return re.sub(r'<[^>]+>', ' ', value)

    @staticmethod
    def _normalize_whitespace(value: str) -> str:
        """Collapse whitespace for deterministic comparisons and summaries."""
        return _WHITESPACE_RE.sub(' ', value.replace('\xa0', ' ')).strip()


def run_saudi_moh_static_probe() -> SaudiMohStaticProbeResult:
    """Convenience entrypoint for the Saudi MOH static-feasibility probe."""
    probe = SaudiMohStaticProbe()
    return probe.probe()
