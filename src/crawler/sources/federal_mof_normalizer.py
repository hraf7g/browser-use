from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Sequence
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.federal_mof_crawler import FederalMOFTableRow
from src.shared.schemas.tender_ingestion import TenderIngestionInput

DUBAI_TIMEZONE = ZoneInfo("Asia/Dubai")


class FederalMOFNormalizationError(ValueError):
    """Base class for Federal MOF normalization failures."""


class FederalMOFRowShapeError(FederalMOFNormalizationError):
    """Raised when an extracted row does not match the expected table shape."""


class FederalMOFDateParseError(FederalMOFNormalizationError):
    """Raised when an expected Federal MOF datetime cannot be parsed."""


def normalize_federal_mof_row(
    *,
    source_id: UUID,
    row: FederalMOFTableRow,
) -> TenderIngestionInput:
    """
    Normalize one raw Federal MOF row into a TenderIngestionInput.

    Deterministic mapping based on verified live table structure:
        - 0: tender reference/id
        - 1: issuing entity
        - 2: title
        - 3: published/opening datetime in Dubai local time
        - 4: closing datetime in Dubai local time
        - 5: action text ("Click here"), ignored

    Notes:
        - preserves Arabic and English text exactly as extracted
        - does not guess missing fields
        - uses the listing page URL as source_url until row-level detail links
          are added
        - uses the row reference as tender_ref when present
    """
    normalized_cells = _normalize_cells(row.cells)

    if len(normalized_cells) < 5:
        raise FederalMOFRowShapeError(
            f"expected at least 5 non-empty cells, got {len(normalized_cells)} "
            f"for row_index={row.row_index}"
        )

    relevant_cells = normalized_cells[:5]
    tender_ref = _none_if_empty(relevant_cells[0])
    issuing_entity = relevant_cells[1]
    title = relevant_cells[2]
    opening_or_published_raw = relevant_cells[3]
    closing_raw = relevant_cells[4]

    if not issuing_entity.strip():
        raise FederalMOFNormalizationError("issuing entity cell must not be empty")

    if not title.strip():
        raise FederalMOFNormalizationError("title cell must not be empty")

    published_at = _parse_federal_mof_datetime(opening_or_published_raw)
    closing_date = _parse_federal_mof_datetime(closing_raw)

    dedupe_key = _build_dedupe_key(
        source_id=source_id,
        source_url=row.page_url,
        tender_ref=tender_ref,
        issuing_entity=issuing_entity,
        title=title,
        published_at=published_at,
        closing_date=closing_date,
    )

    return TenderIngestionInput(
        source_id=source_id,
        source_url=row.page_url,
        title=title,
        issuing_entity=issuing_entity,
        closing_date=closing_date,
        dedupe_key=dedupe_key,
        tender_ref=tender_ref,
        opening_date=published_at,
        published_at=published_at,
        category=None,
        ai_summary=None,
    )


def normalize_federal_mof_rows(
    *,
    source_id: UUID,
    rows: Sequence[FederalMOFTableRow],
) -> tuple[TenderIngestionInput, ...]:
    """Normalize a sequence of raw Federal MOF rows."""
    return tuple(
        normalize_federal_mof_row(
            source_id=source_id,
            row=row,
        )
        for row in rows
    )


def _normalize_cells(cells: Sequence[str]) -> list[str]:
    """Normalize raw cell text while preserving Arabic/English content."""
    normalized: list[str] = []
    for cell in cells:
        cleaned = cell.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _parse_federal_mof_datetime(raw_value: str) -> datetime:
    """
    Parse a Federal MOF Dubai-local datetime and convert it to UTC.

    Expected format: DD/MM/YYYY H:MM:SS AM/PM
    """
    cleaned = raw_value.strip()
    if not cleaned:
        raise FederalMOFDateParseError("datetime cell must not be empty")

    try:
        local_dt = datetime.strptime(cleaned, "%d/%m/%Y %I:%M:%S %p").replace(
            tzinfo=DUBAI_TIMEZONE
        )
    except ValueError as exc:
        raise FederalMOFDateParseError(
            f"could not parse Federal MOF datetime '{cleaned}'"
        ) from exc

    return local_dt.astimezone(UTC)


def _build_dedupe_key(
    *,
    source_id: UUID,
    source_url: str,
    tender_ref: str | None,
    issuing_entity: str,
    title: str,
    published_at: datetime,
    closing_date: datetime,
) -> str:
    """Build a deterministic dedupe key for normalized Federal MOF rows."""
    components = [
        str(source_id),
        source_url.strip().casefold(),
        "" if tender_ref is None else tender_ref.strip().casefold(),
        issuing_entity.strip().casefold(),
        title.strip().casefold(),
        published_at.isoformat(),
        closing_date.isoformat(),
    ]

    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _none_if_empty(value: str) -> str | None:
    """Convert blank strings to None."""
    cleaned = value.strip()
    return cleaned or None
