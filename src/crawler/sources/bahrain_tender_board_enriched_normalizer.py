from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.bahrain_tender_board_config import (
	BAHRAIN_TENDER_BOARD_CONFIG,
)
from src.crawler.sources.bahrain_tender_board_detail_crawler import (
	BahrainTenderBoardDetailItem,
)
from src.shared.schemas.tender_ingestion import TenderIngestionInput

BAHRAIN_TIMEZONE = ZoneInfo('Asia/Bahrain')


class BahrainTenderBoardEnrichedNormalizationError(ValueError):
	"""Base class for Bahrain Tender Board enriched-normalization failures."""


class BahrainTenderBoardEnrichedDateParseError(BahrainTenderBoardEnrichedNormalizationError):
	"""Raised when a visible Bahrain Tender Board date cannot be parsed strictly."""


def normalize_bahrain_tender_board_enriched_item(
	*,
	source_id: UUID,
	item: BahrainTenderBoardDetailItem,
) -> TenderIngestionInput:
	"""
	Normalize one Bahrain Tender Board detail-enriched item into a TenderIngestionInput.

	Deterministic rules:
	    - title prefers detail_title, then falls back to dashboard_title_text
	    - issuing_entity prefers the detail-page field, then the dashboard field,
	      and only then uses the schema-safe platform fallback
	    - tender_ref prefers the detail-page tender number, then the dashboard value
	    - closing_date is parsed strictly from the visible detail-page field
	    - published_at and opening_date are parsed strictly when visible
	    - category uses the detail-page field when visible
	    - source_url uses the public detail URL and falls back to the final URL
	"""
	title = _preferred_text(item.detail_title, item.dashboard_title_text)
	if title is None:
		raise BahrainTenderBoardEnrichedNormalizationError('no non-empty title could be derived')

	source_url = _normalize_source_url(item)
	issuing_entity = _normalize_issuing_entity(item)
	tender_ref = _preferred_text(
		item.detail_tender_number,
		item.dashboard_visible_tender_number,
	)
	closing_date = _parse_optional_bahrain_public_datetime(
		item.detail_closing_date_raw,
		field_name='detail_closing_date_raw',
	)
	published_at = _parse_optional_bahrain_public_datetime(
		item.detail_published_at_raw,
		field_name='detail_published_at_raw',
	)
	opening_date = _parse_optional_bahrain_public_datetime(
		item.detail_opening_date_raw,
		field_name='detail_opening_date_raw',
	)
	category = _preferred_text(item.detail_category)

	dedupe_key = _build_dedupe_key(
		source_id=source_id,
		source_url=source_url,
		title=title,
		issuing_entity=issuing_entity,
		tender_ref=tender_ref,
		closing_date=closing_date,
		opening_date=opening_date,
		published_at=published_at,
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
		published_at=published_at,
		category=category,
		ai_summary=None,
	)


def normalize_bahrain_tender_board_enriched_items(
	*,
	source_id: UUID,
	items: Sequence[BahrainTenderBoardDetailItem],
) -> tuple[TenderIngestionInput, ...]:
	"""Normalize a sequence of Bahrain Tender Board detail-enriched items."""
	return tuple(
		normalize_bahrain_tender_board_enriched_item(
			source_id=source_id,
			item=item,
		)
		for item in items
	)


def _normalize_source_url(item: BahrainTenderBoardDetailItem) -> str:
	"""Prefer the public detail URL and fall back to the resolved final URL."""
	detail_url = item.detail_url.strip()
	if detail_url:
		return detail_url

	final_url = item.final_url.strip()
	if final_url:
		return final_url

	return BAHRAIN_TENDER_BOARD_CONFIG.listing_url


def _normalize_issuing_entity(item: BahrainTenderBoardDetailItem) -> str:
	"""Return the best visible issuing entity or the schema-safe source fallback."""
	issuing_entity = _preferred_text(
		item.detail_issuing_entity,
		item.dashboard_visible_entity,
	)
	if issuing_entity is not None:
		return issuing_entity
	return BAHRAIN_TENDER_BOARD_CONFIG.source_name


def _parse_optional_bahrain_public_datetime(
	raw_value: str | None,
	*,
	field_name: str,
) -> datetime | None:
	"""Parse a visible Bahrain public datetime strictly when present."""
	cleaned = _none_if_empty(raw_value)
	if cleaned is None:
		return None
	return _parse_bahrain_public_datetime(cleaned, field_name=field_name)


def _parse_bahrain_public_datetime(
	raw_value: str,
	*,
	field_name: str,
) -> datetime:
	"""Parse supported Bahrain public datetime formats and convert to UTC."""
	cleaned = raw_value.strip()
	supported_formats = (
		'%d-%m-%Y %I:%M:%S %p',
		'%d-%m-%Y %I:%M %p',
		'%d/%m/%Y %I:%M:%S %p',
		'%d/%m/%Y %I:%M %p',
		'%d-%m-%Y %H:%M:%S',
		'%d-%m-%Y %H:%M',
		'%d/%m/%Y %H:%M:%S',
		'%d/%m/%Y %H:%M',
		'%d-%m-%Y',
		'%d/%m/%Y',
	)

	for date_format in supported_formats:
		try:
			local_dt = datetime.strptime(cleaned, date_format)
		except ValueError:
			continue

		local_dt = local_dt.replace(tzinfo=BAHRAIN_TIMEZONE)
		return local_dt.astimezone(UTC)

	raise BahrainTenderBoardEnrichedDateParseError(f"could not parse Bahrain Tender Board {field_name} '{cleaned}'")


def _build_dedupe_key(
	*,
	source_id: UUID,
	source_url: str,
	title: str,
	issuing_entity: str,
	tender_ref: str | None,
	closing_date: datetime | None,
	opening_date: datetime | None,
	published_at: datetime | None,
	category: str | None,
) -> str:
	"""Build a stable deterministic dedupe key for enriched Bahrain items."""
	components = [
		str(source_id),
		source_url.strip().casefold(),
		title.strip().casefold(),
		issuing_entity.strip().casefold(),
		'' if tender_ref is None else tender_ref.strip().casefold(),
		'' if closing_date is None else closing_date.isoformat(),
		'' if opening_date is None else opening_date.isoformat(),
		'' if published_at is None else published_at.isoformat(),
		'' if category is None else category.strip().casefold(),
	]
	raw_key = '|'.join(components)
	return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


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
