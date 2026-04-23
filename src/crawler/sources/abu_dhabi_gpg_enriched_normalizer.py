from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.abu_dhabi_gpg_config import ABU_DHABI_GPG_CONFIG
from src.crawler.sources.abu_dhabi_gpg_detail_crawler import AbuDhabiGPGDetailItem
from src.shared.schemas.tender_ingestion import TenderIngestionInput

DUBAI_TIMEZONE = ZoneInfo("Asia/Dubai")


class AbuDhabiGPGEnrichedNormalizationError(ValueError):
    """Base class for Abu Dhabi GPG enriched-normalization failures."""


class AbuDhabiGPGEnrichedDateParseError(AbuDhabiGPGEnrichedNormalizationError):
    """Raised when a visible Abu Dhabi GPG detail-page date cannot be parsed strictly."""


def normalize_abu_dhabi_gpg_enriched_item(
    *,
    source_id: UUID,
    item: AbuDhabiGPGDetailItem,
) -> TenderIngestionInput:
    """
    Normalize one Abu Dhabi GPG detail-enriched item into a TenderIngestionInput.

    Deterministic rules:
        - title prefers detail_title, otherwise falls back to widget_title_text
        - issuing_entity prefers detail_issuing_entity; only if absent do we use the
          schema-safe platform fallback
        - tender_ref uses the visible detail tender/reference number when available
        - closing_date prefers detail_closing_date_raw and falls back to the visible
          widget due date when a detail page is unavailable
        - opening_date is parsed strictly from detail_opening_date_raw when visible
        - category prefers detail_category; if absent, uses detail_notice_type; if
          still absent, falls back to the widget category label
        - source_url uses the public detail URL
        - published_at remains None because the sampled public detail pages do not
          expose a clearly visible publication date field
        - description remains intentionally unmapped because there is no clearly safe
          shared ingestion field for it at this step
    """
    title = _preferred_text(item.detail_title, item.widget_title_text)
    if title is None:
        raise AbuDhabiGPGEnrichedNormalizationError("no non-empty title could be derived")

    source_url = _normalize_source_url(item)
    issuing_entity = _normalize_issuing_entity(item)
    tender_ref = _none_if_empty(item.detail_tender_ref)
    closing_date = _normalize_closing_date(item)
    opening_date = _parse_optional_abu_dhabi_public_date(
        item.detail_opening_date_raw,
        field_name="detail_opening_date_raw",
    )
    category = _normalize_category(item)

    dedupe_key = _build_dedupe_key(
        source_id=source_id,
        source_url=source_url,
        title=title,
        issuing_entity=issuing_entity,
        tender_ref=tender_ref,
        closing_date=closing_date,
        opening_date=opening_date,
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
        opening_date=opening_date,
        published_at=None,
        category=category,
        ai_summary=None,
    )


def normalize_abu_dhabi_gpg_enriched_items(
    *,
    source_id: UUID,
    items: Sequence[AbuDhabiGPGDetailItem],
) -> tuple[TenderIngestionInput, ...]:
    """Normalize a sequence of Abu Dhabi GPG detail-enriched items."""
    return tuple(
        normalize_abu_dhabi_gpg_enriched_item(
            source_id=source_id,
            item=item,
        )
        for item in items
    )


def _normalize_source_url(item: AbuDhabiGPGDetailItem) -> str:
    """Prefer the public detail URL and fall back to the final URL if needed."""
    detail_url = item.detail_url.strip()
    if detail_url:
        return detail_url

    final_url = item.final_url.strip()
    if final_url:
        return final_url

    return ABU_DHABI_GPG_CONFIG.listing_url


def _normalize_issuing_entity(item: AbuDhabiGPGDetailItem) -> str:
    """
    Return the visible issuing entity or a schema-safe platform fallback.

    The enriched detail pages usually expose the entity directly. We only fall back
    to the source name if a sampled page omits it and the ingestion schema still
    requires a non-empty issuing_entity.
    """
    issuing_entity = _none_if_empty(item.detail_issuing_entity)
    if issuing_entity is not None:
        return issuing_entity
    return ABU_DHABI_GPG_CONFIG.source_name


def _normalize_category(item: AbuDhabiGPGDetailItem) -> str | None:
    """Prefer detail category, then detail notice type, then the widget category label."""
    detail_category = _none_if_empty(item.detail_category)
    if detail_category is not None:
        return detail_category

    detail_notice_type = _none_if_empty(item.detail_notice_type)
    if detail_notice_type is not None:
        return detail_notice_type

    return _none_if_empty(item.widget_visible_category_label)


def _normalize_closing_date(item: AbuDhabiGPGDetailItem) -> datetime:
    """Prefer detail closing date and fall back to the visible widget due date."""
    detail_closing_date = _parse_optional_abu_dhabi_public_date(
        item.detail_closing_date_raw,
        field_name="detail_closing_date_raw",
    )
    if detail_closing_date is not None:
        return detail_closing_date

    widget_due_date = _parse_optional_abu_dhabi_public_date(
        item.widget_visible_due_date,
        field_name="widget_visible_due_date",
    )
    if widget_due_date is not None:
        return widget_due_date

    raise AbuDhabiGPGEnrichedNormalizationError(
        "no visible closing date could be derived from detail or widget fields"
    )


def _parse_optional_abu_dhabi_public_date(
    raw_value: str | None,
    *,
    field_name: str,
) -> datetime | None:
    """Parse a visible Abu Dhabi GPG public date strictly when present."""
    cleaned = _none_if_empty(raw_value)
    if cleaned is None:
        return None
    return _parse_abu_dhabi_public_date(cleaned, field_name=field_name)


def _parse_abu_dhabi_public_date(
    raw_value: str | None,
    *,
    field_name: str,
) -> datetime:
    """Parse a visible Abu Dhabi GPG public date strictly as Dubai local midnight."""
    cleaned = _none_if_empty(raw_value)
    if cleaned is None:
        raise AbuDhabiGPGEnrichedNormalizationError(f"{field_name} must not be empty")

    local_dt = _parse_supported_abu_dhabi_date_format(cleaned, field_name=field_name)

    return local_dt.astimezone(UTC)


def _parse_supported_abu_dhabi_date_format(
    raw_value: str,
    *,
    field_name: str,
) -> datetime:
    """Parse supported public ADGPG date formats from detail or widget surfaces."""
    for date_format in ("%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(raw_value, date_format).replace(
                tzinfo=DUBAI_TIMEZONE
            )
        except ValueError:
            continue

    raise AbuDhabiGPGEnrichedDateParseError(
        f"could not parse Abu Dhabi GPG {field_name} '{raw_value}'"
    )


def _build_dedupe_key(
    *,
    source_id: UUID,
    source_url: str,
    title: str,
    issuing_entity: str,
    tender_ref: str | None,
    closing_date: datetime,
    opening_date: datetime | None,
    category: str | None,
) -> str:
    """Build a stable deterministic dedupe key for enriched Abu Dhabi GPG items."""
    components = [
        str(source_id),
        source_url.strip().casefold(),
        title.strip().casefold(),
        issuing_entity.strip().casefold(),
        "" if tender_ref is None else tender_ref.strip().casefold(),
        closing_date.isoformat(),
        "" if opening_date is None else opening_date.isoformat(),
        "" if category is None else category.strip().casefold(),
    ]
    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _preferred_text(*values: str | None) -> str | None:
    """Return the first non-empty stripped text value."""
    for value in values:
        cleaned = _none_if_empty(value)
        if cleaned is not None:
            return cleaned
    return None


def _none_if_empty(value: str | None) -> str | None:
    """Convert blank strings to None."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
