from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from src.crawler.sources.federal_mof_crawler import FederalMOFTableRow
from src.shared.schemas.tender_ingestion import TenderIngestionInput

DUBAI_TIMEZONE = ZoneInfo('Asia/Dubai')


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
	    - common 6-cell shape:
	      0: tender reference/id
	      1: issuing entity
	      2: title
	      3: published/opening datetime in Dubai local time
	      4: closing datetime in Dubai local time
	      5: action text ("Click here"), ignored
	    - alternate 5-cell shape:
	      0: tender reference/id
	      1: title
	      2: published/opening datetime in Dubai local time
	      3: closing datetime in Dubai local time
	      4: action text ("Click here"), ignored
	      In that case the issuing entity is not visibly present and falls back
	      to the official source name required by the ingestion schema.

	Notes:
	    - preserves Arabic and English text exactly as extracted
	    - does not guess missing fields
	    - prefers the visible row action href as source_url when available
	    - uses the row reference as tender_ref when present
	"""
	normalized_cells = _normalize_cells(row.cells)

	if len(normalized_cells) < 5:
		raise FederalMOFRowShapeError(
			f'expected at least 5 non-empty cells, got {len(normalized_cells)} for row_index={row.row_index}'
		)

	mapped_row = _map_federal_mof_row_shape(
		normalized_cells=normalized_cells,
		row_index=row.row_index,
	)
	tender_ref = mapped_row.tender_ref
	issuing_entity = mapped_row.issuing_entity
	title = mapped_row.title
	opening_or_published_raw = mapped_row.published_at_raw
	closing_raw = mapped_row.closing_date_raw

	if not issuing_entity.strip():
		raise FederalMOFNormalizationError('issuing entity cell must not be empty')

	if not title.strip():
		raise FederalMOFNormalizationError('title cell must not be empty')

	published_at = _parse_federal_mof_datetime(opening_or_published_raw)
	closing_date = _parse_federal_mof_datetime(closing_raw)
	source_url = _normalize_source_url(row)

	dedupe_key = _build_dedupe_key(
		source_id=source_id,
		source_url=source_url,
		tender_ref=tender_ref,
		issuing_entity=issuing_entity,
		title=title,
		published_at=published_at,
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


class _MappedFederalMOFRowShape:
	"""Internal mapped Federal MOF row shape after deterministic validation."""

	def __init__(
		self,
		*,
		tender_ref: str | None,
		issuing_entity: str,
		title: str,
		published_at_raw: str,
		closing_date_raw: str,
	) -> None:
		self.tender_ref = tender_ref
		self.issuing_entity = issuing_entity
		self.title = title
		self.published_at_raw = published_at_raw
		self.closing_date_raw = closing_date_raw


def _map_federal_mof_row_shape(
	*,
	normalized_cells: list[str],
	row_index: int,
) -> _MappedFederalMOFRowShape:
	"""Map one live Federal MOF row into a validated deterministic shape."""
	action_text = normalized_cells[-1].casefold()
	if 'click here' not in action_text:
		raise FederalMOFRowShapeError(f'unexpected action cell for row_index={row_index}: {normalized_cells[-1]!r}')

	if len(normalized_cells) >= 6:
		return _MappedFederalMOFRowShape(
			tender_ref=_none_if_empty(normalized_cells[0]),
			issuing_entity=normalized_cells[1],
			title=normalized_cells[2],
			published_at_raw=normalized_cells[3],
			closing_date_raw=normalized_cells[4],
		)

	if len(normalized_cells) == 5:
		return _MappedFederalMOFRowShape(
			tender_ref=_none_if_empty(normalized_cells[0]),
			issuing_entity='Federal MOF',
			title=normalized_cells[1],
			published_at_raw=normalized_cells[2],
			closing_date_raw=normalized_cells[3],
		)

	raise FederalMOFRowShapeError(
		f'unsupported Federal MOF row shape with {len(normalized_cells)} cells for row_index={row_index}'
	)


def _normalize_cells(cells: Sequence[str]) -> list[str]:
	"""Normalize raw cell text while preserving Arabic/English content."""
	normalized: list[str] = []
	for cell in cells:
		cleaned = cell.strip()
		if cleaned:
			normalized.append(cleaned)
	return normalized


def _normalize_source_url(row: FederalMOFTableRow) -> str:
	"""Prefer the row action href and fall back to the listing page URL."""
	action_href = _none_if_empty(row.action_href) if row.action_href is not None else None
	if action_href is not None:
		return action_href
	return row.page_url


def _parse_federal_mof_datetime(raw_value: str) -> datetime:
	"""
	Parse a Federal MOF Dubai-local datetime and convert it to UTC.

	Expected format: DD/MM/YYYY H:MM:SS AM/PM
	"""
	cleaned = raw_value.strip()
	if not cleaned:
		raise FederalMOFDateParseError('datetime cell must not be empty')

	try:
		local_dt = datetime.strptime(cleaned, '%d/%m/%Y %I:%M:%S %p').replace(tzinfo=DUBAI_TIMEZONE)
	except ValueError as exc:
		raise FederalMOFDateParseError(f"could not parse Federal MOF datetime '{cleaned}'") from exc

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
		'' if tender_ref is None else tender_ref.strip().casefold(),
		issuing_entity.strip().casefold(),
		title.strip().casefold(),
		published_at.isoformat(),
		closing_date.isoformat(),
	]

	raw_key = '|'.join(components)
	return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()


def _none_if_empty(value: str) -> str | None:
	"""Convert blank strings to None."""
	cleaned = value.strip()
	return cleaned or None
