from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.saudi_misa_config import SAUDI_MISA_CONFIG
from src.crawler.sources.saudi_misa_crawler import SaudiMisaRawItem
from src.shared.schemas.tender_ingestion import TenderIngestionInput

RIYADH_TIMEZONE = ZoneInfo("Asia/Riyadh")
ARABIC_MONTHS: dict[str, int] = {
    "يناير": 1,
    "فبراير": 2,
    "مارس": 3,
    "أبريل": 4,
    "ابريل": 4,
    "مايو": 5,
    "يونيو": 6,
    "يوليو": 7,
    "أغسطس": 8,
    "اغسطس": 8,
    "سبتمبر": 9,
    "أكتوبر": 10,
    "اكتوبر": 10,
    "نوفمبر": 11,
    "ديسمبر": 12,
}
ARABIC_INDIC_DIGIT_TRANSLATION = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
class SaudiMisaNormalizationError(ValueError):
    """Base class for Saudi MISA normalization failures."""


class SaudiMisaDateParseError(SaudiMisaNormalizationError):
    """Raised when a visible Saudi MISA date cannot be parsed strictly."""


def normalize_saudi_misa_item(
    *,
    source_id: UUID,
    item: SaudiMisaRawItem,
) -> TenderIngestionInput:
    """
    Normalize one Saudi MISA raw item into a TenderIngestionInput.

    Deterministic rules:
        - title comes directly from visible title_text
        - tender_ref comes directly from visible_reference_number when present
        - source_url preserves the visible Etimad detail URL exactly
        - issuing_entity uses the page-visible official entity name `MISA`
          because the procurements page is the official Ministry of Investment
          source and the ingestion schema requires a concrete issuer field
        - category remains None because no visible field has a clearly safe shared fit
        - published_at is parsed strictly from visible_offering_date (`تاريخ الطرح`) when present
        - closing_date is parsed strictly from visible_bid_deadline when present
        - rows with no visible bid deadline keep closing_date as None
        - opening_date remains None because the public competitions table does not
          expose a clearly distinct safe opening-date field
    """
    title = item.title_text.strip()
    if not title:
        raise SaudiMisaNormalizationError("title_text must not be empty")

    source_url = _normalize_source_url(item)
    tender_ref = _none_if_empty(item.visible_reference_number)
    issuing_entity = "MISA"
    published_at = _parse_optional_saudi_misa_visible_date(
        item.visible_offering_date,
        field_name="visible_offering_date",
    )
    closing_date = _parse_optional_saudi_misa_visible_date(
        item.visible_bid_deadline,
        field_name="visible_bid_deadline",
    )
    dedupe_key = _build_dedupe_key(
        source_id=source_id,
        source_url=source_url,
        title=title,
        issuing_entity=issuing_entity,
        tender_ref=tender_ref,
        closing_date=closing_date,
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
        category=None,
        ai_summary=None,
    )


def normalize_saudi_misa_items(
    *,
    source_id: UUID,
    items: Sequence[SaudiMisaRawItem],
) -> tuple[TenderIngestionInput, ...]:
    """Normalize a sequence of raw Saudi MISA items."""
    return tuple(
        normalize_saudi_misa_item(
            source_id=source_id,
            item=item,
        )
        for item in items
    )


def _normalize_source_url(item: SaudiMisaRawItem) -> str:
    """Prefer the visible Etimad detail URL and fall back to the page URL only if needed."""
    detail_url = item.detail_url.strip()
    if detail_url:
        return detail_url

    page_url = item.page_url.strip()
    if page_url:
        return page_url

    return SAUDI_MISA_CONFIG.listing_url


def _build_dedupe_key(
    *,
    source_id: UUID,
    source_url: str,
    title: str,
    issuing_entity: str,
    tender_ref: str | None,
    closing_date: datetime | None,
) -> str:
    """Build a stable deterministic dedupe key for normalized Saudi MISA rows."""
    components = [
        str(source_id),
        source_url.strip().casefold(),
        title.strip().casefold(),
        issuing_entity.strip().casefold(),
        "" if tender_ref is None else tender_ref.strip().casefold(),
        "" if closing_date is None else closing_date.isoformat(),
    ]
    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _parse_saudi_misa_visible_date(raw_value: str | None, *, field_name: str) -> datetime:
    """Parse one visible Saudi MISA Arabic date strictly as Riyadh local midnight."""
    cleaned = _required_text(raw_value, field_name=field_name)
    normalized = cleaned.translate(ARABIC_INDIC_DIGIT_TRANSLATION)
    parts = _split_saudi_misa_date_parts(normalized)
    if parts is None:
        raise SaudiMisaDateParseError(
            f"could not parse Saudi MISA {field_name} '{cleaned}'"
        )

    day_text, month_text, year_text = parts
    month_number = ARABIC_MONTHS.get(month_text)
    if month_number is None:
        raise SaudiMisaDateParseError(
            f"could not parse Saudi MISA {field_name} '{cleaned}'"
        )

    try:
        local_dt = datetime(
            year=int(year_text),
            month=month_number,
            day=int(day_text),
            tzinfo=RIYADH_TIMEZONE,
        )
    except ValueError as exc:
        raise SaudiMisaDateParseError(
            f"could not parse Saudi MISA {field_name} '{cleaned}'"
        ) from exc

    return local_dt.astimezone(UTC)


def _parse_optional_saudi_misa_visible_date(
    raw_value: str | None,
    *,
    field_name: str,
) -> datetime | None:
    """Parse a visible Saudi MISA date when present, otherwise return None."""
    cleaned = _none_if_empty(raw_value)
    if cleaned is None:
        return None
    return _parse_saudi_misa_visible_date(cleaned, field_name=field_name)


def _split_saudi_misa_date_parts(value: str) -> tuple[str, str, str] | None:
    """Split visible Arabic date text across the supported rendered formats."""
    hyphen_parts = [segment.strip() for segment in value.split("-") if segment.strip()]
    if len(hyphen_parts) == 3:
        return hyphen_parts[0], hyphen_parts[1], hyphen_parts[2]

    space_parts = [segment.strip() for segment in value.split() if segment.strip()]
    if len(space_parts) == 3:
        return space_parts[0], space_parts[1], space_parts[2]

    return None


def _required_text(value: str | None, *, field_name: str) -> str:
    """Return required non-empty text for a visible Saudi MISA field."""
    cleaned = _none_if_empty(value)
    if cleaned is None:
        raise SaudiMisaNormalizationError(f"{field_name} must not be empty")
    return cleaned


def _none_if_empty(value: str | None) -> str | None:
    """Convert blank strings to None."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None
