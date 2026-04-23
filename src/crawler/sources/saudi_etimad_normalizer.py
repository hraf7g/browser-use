from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.saudi_etimad_config import SAUDI_ETIMAD_CONFIG
from src.crawler.sources.saudi_etimad_crawler import SaudiEtimadRawItem
from src.shared.schemas.tender_ingestion import TenderIngestionInput

RIYADH_TIMEZONE = ZoneInfo("Asia/Riyadh")
class SaudiEtimadNormalizationError(ValueError):
    """Base class for Saudi Etimad normalization failures."""


class SaudiEtimadDateParseError(SaudiEtimadNormalizationError):
    """Raised when a visible Saudi Etimad date cannot be parsed strictly."""


def normalize_saudi_etimad_item(
    *,
    source_id: UUID,
    item: SaudiEtimadRawItem,
) -> TenderIngestionInput:
    """
    Normalize one Saudi Etimad raw listing item into a TenderIngestionInput.

    Deterministic rules:
        - title comes directly from mapped title_text
        - issuing_entity is preserved when visibly available
        - if issuing_entity is missing, the platform source name is used as the
          safest schema-required fallback without fabricating an organization
        - publication_date is parsed strictly when visible
        - closing_date falls back to publication_date when visible, otherwise remains None
          because the listing often omits a visible closing date entirely
        - category uses the procurement_type_label only when visibly available
        - tender_ref uses visible_reference only when visibly available
        - source_url prefers the detail URL
    """
    title = item.title_text.strip()
    if not title:
        raise SaudiEtimadNormalizationError("title_text must not be empty")

    source_url = _normalize_source_url(item)
    issuing_entity = _normalize_issuing_entity(item)
    published_at = _parse_saudi_publication_date(item.publication_date)
    closing_date = published_at
    category = _none_if_empty(item.procurement_type_label)
    tender_ref = _none_if_empty(item.visible_reference)

    dedupe_key = _build_dedupe_key(
        source_id=source_id,
        source_url=source_url,
        title=title,
        issuing_entity=issuing_entity,
        tender_ref=tender_ref,
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
        published_at=published_at,
        category=category,
        ai_summary=None,
    )


def normalize_saudi_etimad_items(
    *,
    source_id: UUID,
    items: Sequence[SaudiEtimadRawItem],
) -> tuple[TenderIngestionInput, ...]:
    """Normalize a sequence of raw Saudi Etimad listing items."""
    return tuple(
        normalize_saudi_etimad_item(
            source_id=source_id,
            item=item,
        )
        for item in items
    )


def _normalize_source_url(item: SaudiEtimadRawItem) -> str:
    """Prefer the item detail URL and fall back to the page URL only if needed."""
    detail_url = item.detail_url.strip()
    if detail_url:
        return detail_url

    page_url = item.page_url.strip()
    if page_url:
        return page_url

    return SAUDI_ETIMAD_CONFIG.listing_url


def _normalize_issuing_entity(item: SaudiEtimadRawItem) -> str:
    """
    Return the visible issuing entity or a schema-safe platform fallback.

    The listing frequently omits the entity line entirely. The ingestion schema
    requires a non-empty issuing_entity, so the platform source name is used as
    the safest deterministic fallback without inventing an organization.
    """
    issuing_entity = _none_if_empty(item.issuing_entity)
    if issuing_entity is not None:
        return issuing_entity
    return SAUDI_ETIMAD_CONFIG.source_name


def _parse_saudi_publication_date(raw_value: str | None) -> datetime | None:
    """Parse a visible Saudi Etimad publication date strictly as Riyadh local midnight."""
    cleaned = _none_if_empty(raw_value)
    if cleaned is None:
        return None

    try:
        local_dt = datetime.strptime(cleaned, "%Y-%m-%d").replace(
            tzinfo=RIYADH_TIMEZONE
        )
    except ValueError as exc:
        raise SaudiEtimadDateParseError(
            f"could not parse Saudi Etimad publication date '{cleaned}'"
        ) from exc

    return local_dt.astimezone(UTC)


def _build_dedupe_key(
    *,
    source_id: UUID,
    source_url: str,
    title: str,
    issuing_entity: str,
    tender_ref: str | None,
) -> str:
    """Build a stable deterministic dedupe key for normalized Saudi Etimad items."""
    components = [
        str(source_id),
        source_url.strip().casefold(),
        title.strip().casefold(),
        issuing_entity.strip().casefold(),
        "" if tender_ref is None else tender_ref.strip().casefold(),
    ]
    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _none_if_empty(value: str | None) -> str | None:
    """Convert blank strings to None."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
