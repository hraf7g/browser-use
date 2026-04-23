from __future__ import annotations

import hashlib
from typing import Sequence
from uuid import UUID

from src.crawler.sources.bahrain_tender_board_config import (
    BAHRAIN_TENDER_BOARD_CONFIG,
)
from src.crawler.sources.bahrain_tender_board_crawler import BahrainTenderBoardRawItem
from src.shared.schemas.tender_ingestion import TenderIngestionInput


class BahrainTenderBoardNormalizationError(ValueError):
    """Base class for Bahrain Tender Board normalization failures."""


def normalize_bahrain_tender_board_item(
    *,
    source_id: UUID,
    item: BahrainTenderBoardRawItem,
) -> TenderIngestionInput:
    """
    Normalize one Bahrain Tender Board raw item into a TenderIngestionInput.

    Deterministic rules:
        - title comes directly from mapped title_text
        - issuing_entity is preserved when visibly available
        - if issuing_entity is missing, the platform source name is used as the
          safest schema-required fallback without inventing an organization
        - tender_ref uses visible_tender_number only when visibly available
        - PA reference remains intentionally unmapped because there is no clearly
          safe existing ingestion field for it yet
        - source_url uses the public detail URL
        - category remains None because the dashboard exposes no safe category field
        - visible_time_left is never converted into a datetime; closing_date remains
          None because the public dashboard does not expose a real one
    """
    title = item.title_text.strip()
    if not title:
        raise BahrainTenderBoardNormalizationError("title_text must not be empty")

    source_url = _normalize_source_url(item)
    issuing_entity = _normalize_issuing_entity(item)
    tender_ref = _none_if_empty(item.visible_tender_number)

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
        closing_date=None,
        dedupe_key=dedupe_key,
        tender_ref=tender_ref,
        opening_date=None,
        published_at=None,
        category=None,
        ai_summary=None,
    )


def normalize_bahrain_tender_board_items(
    *,
    source_id: UUID,
    items: Sequence[BahrainTenderBoardRawItem],
) -> tuple[TenderIngestionInput, ...]:
    """Normalize a sequence of raw Bahrain Tender Board items."""
    return tuple(
        normalize_bahrain_tender_board_item(
            source_id=source_id,
            item=item,
        )
        for item in items
    )


def _normalize_source_url(item: BahrainTenderBoardRawItem) -> str:
    """Prefer the public item detail URL and fall back to the page URL only if needed."""
    detail_url = item.detail_url.strip()
    if detail_url:
        return detail_url

    page_url = item.page_url.strip()
    if page_url:
        return page_url

    return BAHRAIN_TENDER_BOARD_CONFIG.listing_url


def _normalize_issuing_entity(item: BahrainTenderBoardRawItem) -> str:
    """
    Return the visible issuing entity or a schema-safe platform fallback.

    The dashboard usually exposes the entity, but the ingestion schema requires
    a non-empty issuing_entity, so the platform source name is used as the safest
    deterministic fallback if the row omits it.
    """
    issuing_entity = _none_if_empty(item.visible_entity)
    if issuing_entity is not None:
        return issuing_entity
    return BAHRAIN_TENDER_BOARD_CONFIG.source_name


def _build_dedupe_key(
    *,
    source_id: UUID,
    source_url: str,
    title: str,
    issuing_entity: str,
    tender_ref: str | None,
) -> str:
    """Build a stable deterministic dedupe key for normalized Bahrain dashboard items."""
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
