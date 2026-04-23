from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.saudi_etimad_config import SAUDI_ETIMAD_CONFIG
from src.crawler.sources.saudi_etimad_detail_crawler import SaudiEtimadDetailItem
from src.shared.schemas.tender_ingestion import TenderIngestionInput

RIYADH_TIMEZONE = ZoneInfo('Asia/Riyadh')
ARABIC_INDIC_DIGIT_TRANSLATION = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
_DATE_ONLY_ISO_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
_DATE_ONLY_SLASH_RE = re.compile(r'^\d{2}/\d{2}/\d{4}$')
_DATE_TIME_SLASH_RE = re.compile(r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}$')


class SaudiEtimadEnrichedNormalizationError(ValueError):
	"""Base class for Saudi Etimad enriched-normalization failures."""


class SaudiEtimadEnrichedDateParseError(SaudiEtimadEnrichedNormalizationError):
	"""Raised when a visible Saudi Etimad date cannot be parsed strictly."""


def normalize_saudi_etimad_enriched_item(
	*,
	source_id: UUID,
	item: SaudiEtimadDetailItem,
) -> TenderIngestionInput:
	"""
	Normalize one Saudi Etimad detail-enriched item into a TenderIngestionInput.

	Deterministic rules:
	    - title prefers the detail-page competition title
	    - issuing_entity prefers the detail-page government entity
	    - published_at is parsed only from a visible listing publication date
	    - closing_date and opening_date are parsed only when visibly present on the listing row
	    - tender_ref prefers the visible competition number, then reference number, then the listing reference
	    - category prefers the detail-page competition type, then the listing procurement type
	    - no field is fabricated when the public surfaces do not expose it
	"""
	title = _preferred_text(item.detail_title, item.dashboard_title_text)
	if title is None:
		raise SaudiEtimadEnrichedNormalizationError('no non-empty title could be derived')

	source_url = _normalize_source_url(item)
	issuing_entity = _normalize_issuing_entity(item)
	published_at = _parse_optional_saudi_etimad_visible_date(
		item.dashboard_publication_date,
		field_name='dashboard_publication_date',
	)
	closing_date = _parse_optional_saudi_etimad_visible_date(
		item.dashboard_visible_closing_date_raw,
		field_name='dashboard_visible_closing_date_raw',
	)
	opening_date = _parse_optional_saudi_etimad_visible_date(
		item.dashboard_visible_opening_date_raw,
		field_name='dashboard_visible_opening_date_raw',
	)
	category = _preferred_text(item.detail_procurement_type, item.dashboard_procurement_type_label)
	tender_ref = _normalize_tender_ref(item)

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


def normalize_saudi_etimad_enriched_items(
	*,
	source_id: UUID,
	items: Sequence[SaudiEtimadDetailItem],
) -> tuple[TenderIngestionInput, ...]:
	"""Normalize a sequence of Saudi Etimad detail-enriched items."""
	return tuple(
		normalize_saudi_etimad_enriched_item(
			source_id=source_id,
			item=item,
		)
		for item in items
	)


def _normalize_source_url(item: SaudiEtimadDetailItem) -> str:
	"""Prefer the public detail URL and fall back to the final URL if needed."""
	detail_url = item.detail_url.strip()
	if detail_url:
		return detail_url

	final_url = item.final_url.strip()
	if final_url:
		return final_url

	return SAUDI_ETIMAD_CONFIG.listing_url


def _normalize_issuing_entity(item: SaudiEtimadDetailItem) -> str:
	"""Return the visible issuing entity or a schema-safe platform fallback."""
	issuing_entity = _preferred_text(item.detail_issuing_entity, item.dashboard_issuing_entity)
	if issuing_entity is not None:
		return issuing_entity
	return SAUDI_ETIMAD_CONFIG.source_name


def _normalize_tender_ref(item: SaudiEtimadDetailItem) -> str | None:
	"""Prefer the competition number, then the reference number, then the listing reference."""
	return _preferred_tender_ref(
		item.detail_competition_number,
		item.detail_reference_number,
		item.dashboard_visible_reference,
	)


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


def _parse_optional_saudi_etimad_visible_date(
	raw_value: str | None,
	*,
	field_name: str,
) -> datetime | None:
	"""Parse a visible Saudi Etimad date when present, otherwise return None."""
	cleaned = _none_if_empty(raw_value)
	if cleaned is None:
		return None
	return _parse_saudi_etimad_visible_date(cleaned, field_name=field_name)


def _parse_saudi_etimad_visible_date(raw_value: str, *, field_name: str) -> datetime:
	"""Parse a visible Saudi Etimad date strictly in the supported public formats."""
	cleaned = raw_value.strip().translate(ARABIC_INDIC_DIGIT_TRANSLATION)

	try:
		if _DATE_ONLY_ISO_RE.fullmatch(cleaned):
			local_dt = datetime.strptime(cleaned, '%Y-%m-%d').replace(tzinfo=RIYADH_TIMEZONE)
			return local_dt.astimezone(UTC)
		if _DATE_ONLY_SLASH_RE.fullmatch(cleaned):
			local_dt = datetime.strptime(cleaned, '%d/%m/%Y').replace(tzinfo=RIYADH_TIMEZONE)
			return local_dt.astimezone(UTC)
		if _DATE_TIME_SLASH_RE.fullmatch(cleaned):
			local_dt = datetime.strptime(cleaned, '%d/%m/%Y %H:%M').replace(tzinfo=RIYADH_TIMEZONE)
			return local_dt.astimezone(UTC)
	except ValueError as exc:
		raise SaudiEtimadEnrichedDateParseError(f"could not parse Saudi Etimad {field_name} '{raw_value}'") from exc

	raise SaudiEtimadEnrichedDateParseError(f"could not parse Saudi Etimad {field_name} '{raw_value}'")


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
	"""Build a stable deterministic dedupe key for enriched Saudi Etimad items."""
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
