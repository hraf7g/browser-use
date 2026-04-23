from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.oman_tender_board_crawler import OmanTenderBoardRawItem
from src.shared.schemas.tender_ingestion import TenderIngestionInput

MUSCAT_TIMEZONE = ZoneInfo('Asia/Muscat')


class OmanTenderBoardNormalizationError(ValueError):
	"""Base class for Oman Tender Board normalization failures."""


class OmanTenderBoardDateParseError(OmanTenderBoardNormalizationError):
	"""Raised when a visible Oman Tender Board date cannot be parsed strictly."""


def normalize_oman_tender_board_item(
	*,
	source_id: UUID,
	item: OmanTenderBoardRawItem,
) -> TenderIngestionInput:
	"""
	Normalize one Oman Tender Board raw row into a TenderIngestionInput.

	Deterministic rules:
	    - title comes directly from mapped title_text
	    - issuing_entity comes from visible_entity
	    - tender_ref comes from visible_tender_number
	    - category prefers visible_procurement_category and falls back to visible_tender_type
	      when the procurement category cell is absent
	    - source_url uses the public detail URL
	    - closing_date is parsed strictly from visible_bid_closing_date
	    - visible_sales_end_date remains unmapped because there is no clearly safe shared field for it
	    - opening_date and published_at remain None because the public row does not expose those fields
	"""
	title = item.title_text.strip()
	if not title:
		raise OmanTenderBoardNormalizationError('title_text must not be empty')

	issuing_entity = _required_text(item.visible_entity, field_name='visible_entity')
	tender_ref = _required_text(item.visible_tender_number, field_name='visible_tender_number')
	category = _preferred_text(
		item.visible_procurement_category,
		item.visible_tender_type,
	)
	closing_date = _parse_oman_visible_date(
		item.visible_bid_closing_date,
		field_name='visible_bid_closing_date',
	)
	source_url = _normalize_source_url(item)

	dedupe_key = _build_dedupe_key(
		source_id=source_id,
		source_url=source_url,
		tender_ref=tender_ref,
		title=title,
		issuing_entity=issuing_entity,
		closing_date=closing_date,
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
		opening_date=None,
		published_at=None,
		category=category,
		ai_summary=None,
	)


def normalize_oman_tender_board_items(
	*,
	source_id: UUID,
	items: Sequence[OmanTenderBoardRawItem],
) -> tuple[TenderIngestionInput, ...]:
	"""Normalize a sequence of raw Oman Tender Board items."""
	return tuple(
		normalize_oman_tender_board_item(
			source_id=source_id,
			item=item,
		)
		for item in items
	)


def _normalize_source_url(item: OmanTenderBoardRawItem) -> str:
	"""Prefer the item detail URL and fall back to the page URL only if needed."""
	detail_url = item.detail_url.strip()
	if detail_url:
		return detail_url

	page_url = item.page_url.strip()
	if page_url:
		return page_url

	raise OmanTenderBoardNormalizationError('source_url could not be derived')


def _parse_oman_visible_date(raw_value: str | None, *, field_name: str) -> datetime:
	"""Parse a visible Oman public row date strictly as Muscat local midnight."""
	cleaned = _required_text(raw_value, field_name=field_name)

	try:
		local_dt = datetime.strptime(cleaned, '%d-%m-%Y').replace(tzinfo=MUSCAT_TIMEZONE)
	except ValueError as exc:
		raise OmanTenderBoardDateParseError(f"could not parse Oman Tender Board {field_name} '{cleaned}'") from exc

	return local_dt.astimezone(UTC)


def _build_dedupe_key(
	*,
	source_id: UUID,
	source_url: str,
	tender_ref: str,
	title: str,
	issuing_entity: str,
	closing_date: datetime,
	category: str | None,
) -> str:
	"""Build a stable deterministic dedupe key for normalized Oman rows."""
	components = [
		str(source_id),
		source_url.strip().casefold(),
		tender_ref.strip().casefold(),
		title.strip().casefold(),
		issuing_entity.strip().casefold(),
		closing_date.isoformat(),
		'' if category is None else category.strip().casefold(),
	]
	raw_key = '|'.join(components)
	return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


def _required_text(value: str | None, *, field_name: str) -> str:
	"""Return required non-empty text for a visible Oman row field."""
	cleaned = _none_if_empty(value)
	if cleaned is None:
		raise OmanTenderBoardNormalizationError(f'{field_name} must not be empty')
	return cleaned


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
