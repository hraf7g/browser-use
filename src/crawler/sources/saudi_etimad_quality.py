from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.crawler.sources.saudi_etimad_config import SAUDI_ETIMAD_CONFIG
from src.shared.schemas.tender_ingestion import TenderIngestionInput
from src.shared.text.multilingual import (
    MultilingualTextSnapshot,
    build_multilingual_snapshot,
)

CRYPTO_OR_PLACEHOLDER_TITLES = {
    "vor",
    "misc",
    "other",
    "n/a",
    "na",
    "-",
    "--",
}


@dataclass(frozen=True)
class SaudiEtimadQualityAssessment:
    """
    Deterministic quality assessment for one normalized Saudi Etimad payload.

    Notes:
        - This does not mutate the normalized payload.
        - This does not guess or rewrite fields.
        - It only scores and flags data quality risks for downstream handling.
    """

    payload: TenderIngestionInput
    quality_score: int
    is_review_required: bool
    quality_flags: tuple[str, ...]


def assess_saudi_etimad_payload(
    payload: TenderIngestionInput,
) -> SaudiEtimadQualityAssessment:
    """
    Assess one normalized Saudi Etimad payload for downstream data quality risk.

    Scoring model:
        - starts at 100
        - subtracts deterministic penalties for weak, missing, or fallback-driven fields
        - clamps final score into [0, 100]

    Review model:
        - review required if score < 70
        - review required if any high-signal flags are present
    """
    flags: list[str] = []
    score = 100

    title_snapshot = build_multilingual_snapshot(payload.title)
    entity_snapshot = build_multilingual_snapshot(payload.issuing_entity)
    category_snapshot = (
        None if payload.category is None else build_multilingual_snapshot(payload.category)
    )
    tender_ref_snapshot = (
        None if payload.tender_ref is None else build_multilingual_snapshot(payload.tender_ref)
    )

    title_word_count = len(title_snapshot.tokens)
    title_has_meaningful_letters = title_snapshot.script != "unknown"

    if len(title_snapshot.collapsed) < 8:
        flags.append("title_too_short")
        score -= 35
    elif len(title_snapshot.collapsed) < 14:
        flags.append("title_short")
        score -= 12

    if title_word_count <= 1:
        flags.append("title_single_token")
        score -= 20
    elif title_word_count == 2:
        flags.append("title_low_word_count")
        score -= 8

    if not title_has_meaningful_letters:
        flags.append("title_missing_letters")
        score -= 35

    if title_snapshot.collapsed in CRYPTO_OR_PLACEHOLDER_TITLES:
        flags.append("title_placeholder_like")
        score -= 35

    if _looks_like_reference_only(title_snapshot):
        flags.append("title_reference_like")
        score -= 30

    if len(entity_snapshot.collapsed) < 3:
        flags.append("issuing_entity_too_short")
        score -= 25

    if entity_snapshot.script == "unknown":
        flags.append("issuing_entity_missing_letters")
        score -= 25

    if payload.issuing_entity == SAUDI_ETIMAD_CONFIG.source_name:
        flags.append("issuing_entity_platform_fallback")
        score -= 30

    if payload.closing_date is None:
        flags.append("closing_date_missing")
        score -= 35

    if payload.published_at is None:
        flags.append("published_at_missing")
        score -= 12

    if tender_ref_snapshot is None:
        flags.append("tender_ref_missing")
        score -= 12

    if category_snapshot is None:
        flags.append("category_missing")
        score -= 6

    if payload.source_url.strip() != payload.source_url:
        flags.append("source_url_untrimmed")
        score -= 5

    quality_score = max(0, min(100, score))

    high_signal_flags = {
        "title_too_short",
        "title_missing_letters",
        "title_placeholder_like",
        "title_reference_like",
        "issuing_entity_too_short",
        "issuing_entity_missing_letters",
        "issuing_entity_platform_fallback",
        "closing_date_missing",
    }

    is_review_required = (
        quality_score < 70 or any(flag in high_signal_flags for flag in flags)
    )

    return SaudiEtimadQualityAssessment(
        payload=payload,
        quality_score=quality_score,
        is_review_required=is_review_required,
        quality_flags=tuple(flags),
    )


def assess_saudi_etimad_payloads(
    payloads: Sequence[TenderIngestionInput],
) -> tuple[SaudiEtimadQualityAssessment, ...]:
    """Assess a sequence of normalized Saudi Etimad payloads."""
    return tuple(assess_saudi_etimad_payload(payload) for payload in payloads)


def _looks_like_reference_only(snapshot: MultilingualTextSnapshot) -> bool:
    """
    Return whether a title looks like a reference/token rather than a real title.

    Examples this should catch:
        - 60019910
        - REQ 12607678
        - INS-26-896914
    """
    value = snapshot.collapsed
    if not value:
        return False

    if snapshot.script != "unknown":
        alphabetic_tokens = [
            token
            for token in snapshot.tokens
            if any(character.isalpha() for character in token)
        ]
        if len(alphabetic_tokens) > 1:
            return False

    allowed_chars_only = all(
        character.isalnum() or character in {" ", "-", "/", "_", "#"}
        for character in value
    )
    if not allowed_chars_only:
        return False

    digit_count = sum(1 for character in value if character.isdigit())
    return digit_count >= max(4, len(value) // 3)
