from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.qatar_monaqasat_config import QATAR_MONAQASAT_CONFIG
from src.crawler.sources.qatar_monaqasat_detail_crawler import (
	QatarMonaqasatDetailItem,
)
from src.shared.schemas.tender_ingestion import TenderIngestionInput

QATAR_TIMEZONE = ZoneInfo('Asia/Qatar')


class QatarMonaqasatNormalizationError(ValueError):
	"""Base class for Qatar Monaqasat enriched-normalization failures."""


class QatarMonaqasatDateParseError(QatarMonaqasatNormalizationError):
	"""Raised when a visible Qatar Monaqasat date cannot be parsed strictly."""


def normalize_qatar_monaqasat_item(
	*,
	source_id: UUID,
	item: QatarMonaqasatDetailItem,
) -> TenderIngestionInput:
	"""
	Normalize one Qatar Monaqasat detail-enriched item into a TenderIngestionInput.
	"""
	title = _preferred_text(item.detail_title, item.dashboard_title_text)
	if title is None:
		raise QatarMonaqasatNormalizationError('no non-empty title could be derived')

	source_url = _normalize_source_url(item)
	issuing_entity = _normalize_issuing_entity(item)
	tender_ref = _preferred_text(
		item.detail_tender_number,
		item.dashboard_visible_reference,
	)
	closing_date = _parse_optional_qatar_public_date(
		item.detail_closing_date_raw,
		field_name='detail_closing_date_raw',
	)
	published_at = _parse_optional_qatar_public_date(
		item.detail_publish_date_raw,
		field_name='detail_publish_date_raw',
	)
	opening_date = _parse_optional_qatar_public_date(
		item.detail_opening_date_raw,
		field_name='detail_opening_date_raw',
	)
	category = _preferred_text(
		item.detail_tender_type,
		item.dashboard_visible_tender_type,
		item.detail_request_types,
	)

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


def normalize_qatar_monaqasat_items(
	*,
	source_id: UUID,
	items: Sequence[QatarMonaqasatDetailItem],
) -> tuple[TenderIngestionInput, ...]:
	"""Normalize a sequence of Qatar detail-enriched items."""
	return tuple(
		normalize_qatar_monaqasat_item(
			source_id=source_id,
			item=item,
		)
		for item in items
	)


def _normalize_source_url(item: QatarMonaqasatDetailItem) -> str:
	"""Prefer the public detail URL and fall back to the final URL."""
	detail_url = item.detail_url.strip()
	if detail_url:
		return detail_url

	final_url = item.final_url.strip()
	if final_url:
		return final_url

	return QATAR_MONAQASAT_CONFIG.listing_url


def _normalize_issuing_entity(item: QatarMonaqasatDetailItem) -> str:
	"""Return the best visible issuing entity or the schema-safe source fallback."""
	issuing_entity = _preferred_text(
		item.detail_ministry,
		item.dashboard_visible_ministry,
	)
	if issuing_entity is not None:
		return issuing_entity
	return QATAR_MONAQASAT_CONFIG.source_name


def _parse_optional_qatar_public_date(
	raw_value: str | None,
	*,
	field_name: str,
) -> datetime | None:
	"""Parse a visible Qatar public date strictly when present."""
	cleaned = _none_if_empty(raw_value)
	if cleaned is None:
		return None
	return _parse_qatar_public_date(cleaned, field_name=field_name)


def _parse_qatar_public_date(
	raw_value: str,
	*,
	field_name: str,
) -> datetime:
	"""Parse supported Qatar public date formats and convert to UTC midnight."""
	cleaned = raw_value.strip()
	try:
		local_dt = datetime.strptime(cleaned, '%d/%m/%Y').replace(tzinfo=QATAR_TIMEZONE)
	except ValueError as exc:
		raise QatarMonaqasatDateParseError(f"could not parse Qatar Monaqasat {field_name} '{cleaned}'") from exc

	return local_dt.astimezone(UTC)


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
	"""Build a stable deterministic dedupe key for Qatar items."""
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
