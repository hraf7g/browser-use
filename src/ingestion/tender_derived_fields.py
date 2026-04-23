from __future__ import annotations

from src.shared.industry_taxonomy import classify_industry_codes
from src.shared.text.multilingual import normalize_multilingual_text


def build_tender_search_text(
	*,
	title: str,
	issuing_entity: str,
	category: str | None,
	ai_summary: str | None,
	tender_ref: str | None,
) -> str:
	"""Build deterministic persisted multilingual search text for a tender."""
	parts = [
		title,
		issuing_entity,
		category,
		ai_summary,
		tender_ref,
	]
	normalized_parts = [normalize_multilingual_text(part) for part in parts if isinstance(part, str) and part.strip()]
	return ' '.join(part for part in normalized_parts if part)


def build_tender_industry_codes(
	*,
	category: str | None,
	title: str,
	issuing_entity: str,
	ai_summary: str | None,
	explicit_industry_codes: list[str] | None = None,
) -> list[str]:
	"""Return explicit industry codes when present, otherwise classify deterministically from tender text."""
	if explicit_industry_codes:
		return list(explicit_industry_codes)

	return classify_industry_codes(
		category=category,
		title=title,
		issuing_entity=issuing_entity,
		ai_summary=ai_summary,
	)


def build_primary_industry_code(industry_codes: list[str]) -> str | None:
	"""Return the stable primary industry code for persisted tender rows."""
	if not industry_codes:
		return None
	return industry_codes[0]
