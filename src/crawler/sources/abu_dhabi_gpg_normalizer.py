from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.abu_dhabi_gpg_config import ABU_DHABI_GPG_CONFIG
from src.crawler.sources.abu_dhabi_gpg_crawler import AbuDhabiGPGRawItem
from src.shared.schemas.tender_ingestion import TenderIngestionInput

DUBAI_TIMEZONE = ZoneInfo("Asia/Dubai")


class AbuDhabiGPGNormalizationError(ValueError):
    """Base class for Abu Dhabi GPG normalization failures."""


class AbuDhabiGPGDateParseError(AbuDhabiGPGNormalizationError):
    """Raised when a visible Abu Dhabi GPG due date cannot be parsed strictly."""


def normalize_abu_dhabi_gpg_item(
    *,
    source_id: UUID,
    item: AbuDhabiGPGRawItem,
) -> TenderIngestionInput:
    """
    Normalize one Abu Dhabi GPG homepage-widget item into a TenderIngestionInput.

    Deterministic rules:
        - title comes directly from mapped title_text
        - issuing_entity falls back to the platform source name because the widget
          does not expose a visible issuing entity and the ingestion schema
          requires a non-empty value
        - tender_ref remains None because the widget exposes no visible reference
        - category uses visible_category_label because it is a stable visible field
        - visible_notice_type remains intentionally unmapped because there is no
          clearly safe separate shared ingestion field for it
        - visible_short_description remains intentionally unmapped because there
          is no clearly safe shared ingestion field for it at this step
        - source_url uses the captured public detail URL
        - closing_date is parsed strictly from visible_due_date
        - opening_date and published_at remain None because the widget does not
          expose them visibly
    """
    title = item.title_text.strip()
    if not title:
        raise AbuDhabiGPGNormalizationError("title_text must not be empty")

    source_url = _normalize_source_url(item)
    closing_date = _parse_abu_dhabi_visible_due_date(item.visible_due_date)
    category = _none_if_empty(item.visible_category_label)
    issuing_entity = ABU_DHABI_GPG_CONFIG.source_name
    tender_ref = None

    dedupe_key = _build_dedupe_key(
        source_id=source_id,
        source_url=source_url,
        title=title,
        issuing_entity=issuing_entity,
        closing_date=closing_date,
        category=category,
    )

    return TenderIngestionInput(
        source_id=source_id,
        source_url=source_url,
        title=title,
        issuing_entity=issuing_entity,
        closing_date=closing_date,
        dedupe_key=dedupe_key,
        tender_ref=tender_ref,
        opening_date=None,
        published_at=None,
        category=category,
        ai_summary=None,
    )


def normalize_abu_dhabi_gpg_items(
    *,
    source_id: UUID,
    items: Sequence[AbuDhabiGPGRawItem],
) -> tuple[TenderIngestionInput, ...]:
    """Normalize a sequence of raw Abu Dhabi GPG homepage widget items."""
    return tuple(
        normalize_abu_dhabi_gpg_item(
            source_id=source_id,
            item=item,
        )
        for item in items
    )


def _normalize_source_url(item: AbuDhabiGPGRawItem) -> str:
    """Prefer the widget-derived detail URL and fall back to the page URL if needed."""
    detail_url = item.detail_url.strip()
    if detail_url:
        return detail_url

    page_url = item.page_url.strip()
    if page_url:
        return page_url

    return ABU_DHABI_GPG_CONFIG.listing_url


def _parse_abu_dhabi_visible_due_date(raw_value: str | None) -> datetime:
    """Parse a visible Abu Dhabi GPG due date strictly as Dubai local midnight."""
    cleaned = _none_if_empty(raw_value)
    if cleaned is None:
        raise AbuDhabiGPGNormalizationError("visible_due_date must not be empty")

    try:
        local_dt = datetime.strptime(cleaned, "%d %b %Y").replace(
            tzinfo=DUBAI_TIMEZONE
        )
    except ValueError as exc:
        raise AbuDhabiGPGDateParseError(
            f"could not parse Abu Dhabi GPG visible_due_date '{cleaned}'"
        ) from exc

    return local_dt.astimezone(UTC)


def _build_dedupe_key(
    *,
    source_id: UUID,
    source_url: str,
    title: str,
    issuing_entity: str,
    closing_date: datetime,
    category: str | None,
) -> str:
    """Build a stable deterministic dedupe key for normalized Abu Dhabi GPG items."""
    components = [
        str(source_id),
        source_url.strip().casefold(),
        title.strip().casefold(),
        issuing_entity.strip().casefold(),
        closing_date.isoformat(),
        "" if category is None else category.strip().casefold(),
    ]
    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _none_if_empty(value: str | None) -> str | None:
    """Convert blank strings to None."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
