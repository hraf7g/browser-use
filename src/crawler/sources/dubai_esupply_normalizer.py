from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.dubai_esupply_crawler import DubaiESupplyListingRow
from src.shared.schemas.tender_ingestion import TenderIngestionInput

DUBAI_TIMEZONE = ZoneInfo("Asia/Dubai")
REQ_SLASH_HYPHEN_PATTERN = re.compile(
    r"^(?P<left_ref>REQ\s+\d{4,})\s*/\s*(?P<right_ref>\d{4,})\s*-\s*(?P<title>.+)$",
    re.IGNORECASE,
)
SIMPLE_SLASH_PATTERN = re.compile(
    r"^(?P<ref>[^/]{2,100})\s*/\s*(?P<title>.+)$"
)
NUMERIC_HYPHEN_PATTERN = re.compile(
    r"^(?P<ref>\d{4,})\s*-\s*(?P<title>.+)$"
)
NUMERIC_SPACE_PATTERN = re.compile(
    r"^(?P<ref>\d{4,})\s+(?P<title>.+)$"
)
KNOWN_REFERENCE_PREFIXES = (
    "REQ",
    "RFQ",
    "RFP",
    "RFT",
    "SOQ",
    "IPR",
    "PR",
    "PO",
    "WO",
    "W.O",
    "T",
    "T#",
    "NJI",
)


class DubaiESupplyNormalizationError(ValueError):
    """Base class for Dubai eSupply normalization failures."""


class DubaiESupplyRowShapeError(DubaiESupplyNormalizationError):
    """Raised when an extracted row does not match the expected table shape."""


class DubaiESupplyDateParseError(DubaiESupplyNormalizationError):
    """Raised when a closing date cannot be parsed deterministically."""


def normalize_dubai_esupply_row(
    *,
    source_id: UUID,
    row: DubaiESupplyListingRow,
) -> TenderIngestionInput:
    """
    Normalize one raw Dubai eSupply listing row into a TenderIngestionInput.

    Deterministic assumptions based on verified current listing output:
    - first five non-empty cells are treated as:
        0: currency/price unit (ignored)
        1: issuing entity
        2: title or combined reference/title field
        3: closing date in Dubai local time
        4: category
    - sixth cell exists in the current source shape but is intentionally ignored
      until explicitly modeled in a later controlled step
    """
    normalized_cells = _normalize_cells(row.cells)

    if len(normalized_cells) < 5:
        raise DubaiESupplyRowShapeError(
            f"expected at least 5 non-empty cells, got {len(normalized_cells)} "
            f"for row_index={row.row_index}"
        )

    relevant_cells = normalized_cells[:5]
    issuing_entity = relevant_cells[1]
    raw_title = relevant_cells[2]
    raw_closing_date = relevant_cells[3]
    category = _none_if_empty(relevant_cells[4])
    canonical_source_url = _canonicalize_dubai_source_url(row.page_url)

    tender_ref, title = _split_tender_ref_and_title(raw_title)
    closing_date = _parse_dubai_closing_date(raw_closing_date)

    dedupe_key = _build_dedupe_key(
        source_id=source_id,
        source_url=canonical_source_url,
        issuing_entity=issuing_entity,
        title=title,
        closing_date=closing_date,
        category=category,
        tender_ref=tender_ref,
    )

    return TenderIngestionInput(
        source_id=source_id,
        source_url=canonical_source_url,
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


def normalize_dubai_esupply_rows(
    *,
    source_id: UUID,
    rows: Sequence[DubaiESupplyListingRow],
) -> tuple[TenderIngestionInput, ...]:
    """Normalize a sequence of raw Dubai eSupply rows."""
    return tuple(
        normalize_dubai_esupply_row(
            source_id=source_id,
            row=row,
        )
        for row in rows
    )


def _normalize_cells(cells: Sequence[str]) -> list[str]:
    """Normalize raw cell text while preserving language content."""
    normalized: list[str] = []
    for cell in cells:
        cleaned = cell.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _split_tender_ref_and_title(raw_title: str) -> tuple[str | None, str]:
    """
    Split combined Dubai eSupply title/reference formats deterministically.

    Supported examples:
    - 12607621 / vor
    - 12607620-IVECO TRUCK
    - 12607439 Transportation Maintenance Dept
    - REQ 12607678 / 12607610 -VOR- W.O# INS-26-896914

    If no reliable deterministic split is possible, preserve the full value
    as title and leave tender_ref as None.
    """
    cleaned = raw_title.strip()
    if not cleaned:
        raise DubaiESupplyNormalizationError("title cell must not be empty")

    req_match = REQ_SLASH_HYPHEN_PATTERN.match(cleaned)
    if req_match is not None:
        left_ref = req_match.group("left_ref").strip()
        right_ref = req_match.group("right_ref").strip()
        title = req_match.group("title").strip()
        if (
            left_ref
            and right_ref
            and title
            and _is_high_confidence_tender_ref(left_ref)
            and _is_high_confidence_tender_ref(right_ref)
        ):
            return f"{left_ref} / {right_ref}", title

    slash_match = SIMPLE_SLASH_PATTERN.match(cleaned)
    if slash_match is not None:
        tender_ref = slash_match.group("ref").strip()
        title = slash_match.group("title").strip()
        if tender_ref and title and _is_high_confidence_tender_ref(tender_ref):
            nested_hyphen_match = NUMERIC_HYPHEN_PATTERN.match(title)
            if nested_hyphen_match is not None:
                nested_ref = nested_hyphen_match.group("ref").strip()
                nested_title = nested_hyphen_match.group("title").strip()
                if (
                    nested_ref
                    and nested_title
                    and _is_high_confidence_tender_ref(nested_ref)
                ):
                    return f"{tender_ref} / {nested_ref}", nested_title
            return tender_ref, title

    hyphen_match = NUMERIC_HYPHEN_PATTERN.match(cleaned)
    if hyphen_match is not None:
        tender_ref = hyphen_match.group("ref").strip()
        title = hyphen_match.group("title").strip()
        if tender_ref and title and _is_high_confidence_tender_ref(tender_ref):
            return tender_ref, title

    space_match = NUMERIC_SPACE_PATTERN.match(cleaned)
    if space_match is not None:
        tender_ref = space_match.group("ref").strip()
        title = space_match.group("title").strip()
        if tender_ref and title and _is_high_confidence_tender_ref(tender_ref):
            return tender_ref, title

    return None, cleaned


def _is_high_confidence_tender_ref(value: str) -> bool:
    """
    Return whether a Dubai eSupply reference candidate is safe to persist.

    Heuristics are intentionally conservative:
        - must contain at least 4 digits overall
        - must either start with digits, start with a known procurement prefix,
          or contain structural separators commonly used in references

    This rejects generic department/category labels such as:
        - Med.Equip
        - AJCH
        - Medical Consumable Items
    """
    cleaned = value.strip()
    if not cleaned:
        return False

    digit_count = sum(1 for character in cleaned if character.isdigit())
    if digit_count < 4:
        return False

    if cleaned[0].isdigit():
        return True

    uppercase = cleaned.upper()
    for prefix in KNOWN_REFERENCE_PREFIXES:
        if (
            uppercase == prefix
            or uppercase.startswith(f"{prefix} ")
            or uppercase.startswith(f"{prefix}-")
            or uppercase.startswith(f"{prefix}/")
            or uppercase.startswith(f"{prefix}#")
            or uppercase.startswith(f"{prefix}:")
        ):
            return True

    return any(separator in cleaned for separator in ("/", "-", "#"))


def _parse_dubai_closing_date(raw_value: str) -> datetime:
    """Parse a Dubai-local closing date and convert it to UTC."""
    cleaned = raw_value.strip()
    if not cleaned:
        raise DubaiESupplyDateParseError("closing date cell must not be empty")

    try:
        local_dt = datetime.strptime(cleaned, "%d/%m/%Y %H:%M").replace(
            tzinfo=DUBAI_TIMEZONE
        )
    except ValueError as exc:
        raise DubaiESupplyDateParseError(
            f"could not parse closing date '{cleaned}'"
        ) from exc

    return local_dt.astimezone(UTC)


def _canonicalize_dubai_source_url(source_url: str) -> str:
    """
    Remove known volatile query parameters from the Dubai listing URL.

    Notes:
        - `_ncp` is a live request nonce and is not part of tender identity
        - stable query parameters are preserved in their original order
    """
    cleaned = source_url.strip()
    if not cleaned:
        raise DubaiESupplyNormalizationError("source_url must not be empty")

    split_result = urlsplit(cleaned)
    filtered_query_items = [
        (key, value)
        for key, value in parse_qsl(
            split_result.query,
            keep_blank_values=True,
        )
        if key.casefold() != "_ncp"
    ]
    canonical_query = urlencode(filtered_query_items, doseq=True)
    return urlunsplit(
        (
            split_result.scheme,
            split_result.netloc,
            split_result.path,
            canonical_query,
            split_result.fragment,
        )
    )


def _build_dedupe_key(
    *,
    source_id: UUID,
    source_url: str,
    issuing_entity: str,
    title: str,
    closing_date: datetime,
    category: str | None,
    tender_ref: str | None,
) -> str:
    """Build a deterministic dedupe key for normalized Dubai eSupply rows."""
    components = [
        str(source_id),
        source_url.strip().casefold(),
        issuing_entity.strip().casefold(),
        title.strip().casefold(),
        closing_date.isoformat(),
        "" if category is None else category.strip().casefold(),
        "" if tender_ref is None else tender_ref.strip().casefold(),
    ]
    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _none_if_empty(value: str) -> str | None:
    """Convert blank strings to None."""
    cleaned = value.strip()
    return cleaned or None
