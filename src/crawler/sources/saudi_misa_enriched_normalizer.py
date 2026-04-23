from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.saudi_misa_config import SAUDI_MISA_CONFIG
from src.crawler.sources.saudi_misa_detail_crawler import SaudiMisaDetailItem
from src.shared.schemas.tender_ingestion import TenderIngestionInput

RIYADH_TIMEZONE = ZoneInfo('Asia/Riyadh')


class SaudiMisaEnrichedNormalizationError(ValueError):
	"""Base class for Saudi MISA enriched-normalization failures."""


class SaudiMisaEnrichedDateParseError(SaudiMisaEnrichedNormalizationError):
	"""Raised when a visible Saudi MISA date cannot be parsed strictly."""


def normalize_saudi_misa_enriched_item(
	*,
	source_id: UUID,
	item: SaudiMisaDetailItem,
) -> TenderIngestionInput:
	"""
	Normalize one Saudi MISA detail-enriched item into a TenderIngestionInput.

	Deterministic rules:
	    - title prefers detail_title, otherwise table_title_text
	    - issuing_entity prefers the visible detail-page government entity and
	      only falls back to `MISA` when the detail page does not expose one
	    - tender_ref prefers the visible detail tender number, then the table reference
	    - published_at prefers a visible detail inquiry deadline and falls back to
	      the visible MISA offering date
	    - closing_date prefers a visible detail closing date and falls back to
	      the visible MISA bid deadline
	    - opening_date uses the visible detail opening date only
	    - category prefers visible detail classification, then procurement type
	"""
	title = _preferred_text(item.detail_title, item.table_title_text)
	if title is None:
		raise SaudiMisaEnrichedNormalizationError('no non-empty title could be derived')

	source_url = _normalize_source_url(item)
	issuing_entity = _preferred_text(item.detail_issuing_entity, 'MISA')
	if issuing_entity is None:
		raise SaudiMisaEnrichedNormalizationError('could not derive issuing_entity')

	tender_ref = _preferred_tender_ref(item.detail_tender_ref, item.table_reference_number)
	published_at = _parse_optional_saudi_misa_visible_date(
		_preferred_text(item.detail_published_at_raw, item.table_inquiry_deadline_primary),
		field_name='published_at',
	)
	closing_date = _preferred_datetime(
		_parse_optional_saudi_misa_visible_date(
			item.detail_closing_date_raw,
			field_name='detail_closing_date_raw',
		),
		_parse_optional_saudi_misa_visible_date(
			item.table_inquiry_deadline_secondary,
			field_name='table_inquiry_deadline_secondary',
		),
		_parse_optional_saudi_misa_visible_date(
			item.table_inquiry_deadline_primary,
			field_name='table_inquiry_deadline_primary',
		),
	)
	opening_date = _parse_optional_saudi_misa_visible_date(
		item.detail_opening_date_raw,
		field_name='detail_opening_date_raw',
	)
	category = _preferred_text(item.detail_category, item.detail_procurement_type)

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
		published_at=published_at,
		category=category,
		ai_summary=None,
	)


def normalize_saudi_misa_enriched_items(
	*,
	source_id: UUID,
	items: Sequence[SaudiMisaDetailItem],
) -> tuple[TenderIngestionInput, ...]:
	"""Normalize a sequence of Saudi MISA detail-enriched items."""
	return tuple(
		normalize_saudi_misa_enriched_item(
			source_id=source_id,
			item=item,
		)
		for item in items
	)


def _normalize_source_url(item: SaudiMisaDetailItem) -> str:
	"""Prefer the public detail URL and fall back to the final URL if needed."""
	detail_url = item.detail_url.strip()
	if detail_url:
		return detail_url

	final_url = item.final_url.strip()
	if final_url:
		return final_url

	return SAUDI_MISA_CONFIG.listing_url


def _preferred_tender_ref(*values: str | None) -> str | None:
	"""Return the first non-empty non-placeholder tender reference."""
	for value in values:
		cleaned = _none_if_empty(value)
		if cleaned is None:
			continue
		if cleaned in {'لا يوجد', 'N/A', '-'}:
			continue
		return cleaned
	return None


def _parse_optional_saudi_misa_visible_date(
	raw_value: str | None,
	*,
	field_name: str,
) -> datetime | None:
	"""Parse one visible Saudi MISA Gregorian date when present."""
	cleaned = _none_if_empty(raw_value)
	if cleaned is None:
		return None
	try:
		local_dt = datetime.strptime(cleaned, '%d/%m/%Y').replace(tzinfo=RIYADH_TIMEZONE)
	except ValueError as exc:
		raise SaudiMisaEnrichedDateParseError(f"could not parse Saudi MISA {field_name} '{cleaned}'") from exc
	return local_dt.astimezone(UTC)


def _preferred_datetime(*values: datetime | None) -> datetime | None:
	"""Return the first non-null datetime."""
	for value in values:
		if value is not None:
			return value
	return None


def _build_dedupe_key(
	*,
	source_id: UUID,
	source_url: str,
	title: str,
	issuing_entity: str,
	tender_ref: str | None,
	closing_date: datetime | None,
	opening_date: datetime | None,
	category: str | None,
) -> str:
	"""Build a stable deterministic dedupe key for enriched Saudi MISA items."""
	components = [
		str(source_id),
		source_url.strip().casefold(),
		title.strip().casefold(),
		issuing_entity.strip().casefold(),
		'' if tender_ref is None else tender_ref.strip().casefold(),
		'' if closing_date is None else closing_date.isoformat(),
		'' if opening_date is None else opening_date.isoformat(),
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
