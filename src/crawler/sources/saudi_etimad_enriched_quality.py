from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from src.crawler.sources.saudi_etimad_config import SAUDI_ETIMAD_CONFIG
from src.shared.schemas.tender_ingestion import TenderIngestionInput
from src.shared.text.multilingual import build_multilingual_snapshot

CRYPTO_OR_PLACEHOLDER_TITLES = {
	'vor',
	'misc',
	'other',
	'n/a',
	'na',
	'-',
	'--',
}


@dataclass(frozen=True)
class SaudiEtimadEnrichedQualityAssessment:
	"""Deterministic quality assessment for one enriched Saudi Etimad payload."""

	payload: TenderIngestionInput
	quality_score: int
	is_review_required: bool
	quality_flags: tuple[str, ...]


def assess_saudi_etimad_enriched_payload(
	payload: TenderIngestionInput,
) -> SaudiEtimadEnrichedQualityAssessment:
	"""Assess one enriched Saudi Etimad payload for downstream data quality risk."""
	flags: list[str] = []
	score = 100

	title_snapshot = build_multilingual_snapshot(payload.title)
	entity_snapshot = build_multilingual_snapshot(payload.issuing_entity)
	category_snapshot = None if payload.category is None else build_multilingual_snapshot(payload.category)
	tender_ref_snapshot = None if payload.tender_ref is None else build_multilingual_snapshot(payload.tender_ref)

	if len(title_snapshot.collapsed) < 8:
		flags.append('title_too_short')
		score -= 35
	elif len(title_snapshot.collapsed) < 14:
		flags.append('title_short')
		score -= 12

	if len(title_snapshot.tokens) <= 1:
		flags.append('title_single_token')
		score -= 20
	elif len(title_snapshot.tokens) == 2:
		flags.append('title_low_word_count')
		score -= 8

	if title_snapshot.script == 'unknown':
		flags.append('title_missing_letters')
		score -= 35

	if title_snapshot.collapsed in CRYPTO_OR_PLACEHOLDER_TITLES:
		flags.append('title_placeholder_like')
		score -= 35

	if len(entity_snapshot.collapsed) < 3:
		flags.append('issuing_entity_too_short')
		score -= 25

	if entity_snapshot.script == 'unknown':
		flags.append('issuing_entity_missing_letters')
		score -= 25

	if payload.issuing_entity == SAUDI_ETIMAD_CONFIG.source_name:
		flags.append('issuing_entity_platform_fallback')
		score -= 30

	if payload.closing_date is None:
		flags.append('closing_date_missing')
		score -= 35

	if payload.opening_date is None:
		flags.append('opening_date_missing')
		score -= 8

	if payload.published_at is None:
		flags.append('published_at_missing')
		score -= 12

	if tender_ref_snapshot is None:
		flags.append('tender_ref_missing')
		score -= 12

	if category_snapshot is None:
		flags.append('category_missing')
		score -= 6

	if payload.source_url.strip() != payload.source_url:
		flags.append('source_url_untrimmed')
		score -= 5

	quality_score = max(0, min(100, score))
	high_signal_flags = {
		'title_too_short',
		'title_missing_letters',
		'title_placeholder_like',
		'issuing_entity_too_short',
		'issuing_entity_missing_letters',
		'issuing_entity_platform_fallback',
		'closing_date_missing',
	}
	is_review_required = quality_score < 70 or any(flag in high_signal_flags for flag in flags)

	return SaudiEtimadEnrichedQualityAssessment(
		payload=payload,
		quality_score=quality_score,
		is_review_required=is_review_required,
		quality_flags=tuple(flags),
	)


def assess_saudi_etimad_enriched_payloads(
	payloads: Sequence[TenderIngestionInput],
) -> tuple[SaudiEtimadEnrichedQualityAssessment, ...]:
	"""Assess a sequence of enriched Saudi Etimad payloads."""
	return tuple(assess_saudi_etimad_enriched_payload(payload) for payload in payloads)
