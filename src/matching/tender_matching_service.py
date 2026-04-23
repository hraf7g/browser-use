from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.keyword_profile import KeywordProfile
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.shared.text.multilingual import build_multilingual_snapshot


class TenderNotFoundError(ValueError):
	"""Raised when a requested tender does not exist."""


def match_tender_by_id(
	session: Session,
	*,
	tender_id: UUID,
) -> int:
	"""
	Match a single tender against all active keyword profiles.

	Returns:
	    int: number of new TenderMatch rows created

	Notes:
	    - This function does not commit the transaction.
	    - The caller owns transaction boundaries.
	    - Matching is idempotent for an existing (user_id, tender_id) pair.
	"""
	tender = session.get(Tender, tender_id)
	if tender is None:
		raise TenderNotFoundError(f"tender '{tender_id}' was not found")

	return match_tender(session=session, tender=tender)


def match_tender(
	session: Session,
	*,
	tender: Tender,
) -> int:
	"""
	Match one tender against all active keyword profiles.

	Returns:
	    int: number of new TenderMatch rows created
	"""
	source = session.get(Source, tender.source_id)
	if source is None:
		return 0

	profiles = session.execute(select(KeywordProfile).where(KeywordProfile.alert_enabled.is_(True))).scalars().all()

	if not profiles:
		return 0

	existing_user_ids = set(
		session.execute(select(TenderMatch.user_id).where(TenderMatch.tender_id == tender.id)).scalars().all()
	)

	search_text = _build_tender_search_text(tender)
	search_snapshot = build_multilingual_snapshot(search_text)
	search_token_set = set(search_snapshot.tokens)

	if not search_token_set:
		return 0

	created_count = 0
	for profile in profiles:
		if profile.user_id in existing_user_ids:
			continue

		if not _profile_allows_tender_scope(
			profile=profile,
			tender=tender,
			source=source,
		):
			continue

		matched_keywords = _extract_matched_keywords(
			search_token_set=search_token_set,
			keywords=profile.keywords,
		)

		if not matched_keywords:
			continue

		matched_country_codes = _build_matched_country_codes(
			profile=profile,
			source=source,
		)
		matched_industry_codes = _build_matched_industry_codes(
			profile=profile,
			tender=tender,
		)

		session.add(
			TenderMatch(
				user_id=profile.user_id,
				tender_id=tender.id,
				matched_keywords=matched_keywords,
				matched_country_codes=matched_country_codes,
				matched_industry_codes=matched_industry_codes,
			)
		)
		created_count += 1

	if created_count:
		session.flush()

	return created_count


def match_recent_tenders(
	session: Session,
	*,
	since: datetime,
) -> int:
	"""
	Match all tenders created on or after the given timestamp.

	Returns:
	    int: total number of new TenderMatch rows created
	"""
	tenders = session.execute(select(Tender).where(Tender.created_at >= since).order_by(Tender.created_at.asc())).scalars().all()

	total_created = 0
	for tender in tenders:
		total_created += match_tender(session=session, tender=tender)

	return total_created


def match_tenders_updated_since(
	session: Session,
	*,
	since: datetime,
) -> int:
	"""
	Match all tenders updated on or after the given timestamp.

	Returns:
	    int: total number of new TenderMatch rows created

	Notes:
	    - Uses Tender.updated_at as the scheduler-safe incremental boundary.
	    - Matching remains idempotent for an existing (user_id, tender_id) pair.
	    - Ordering is deterministic by updated_at asc, then id asc.
	"""
	tenders = (
		session.execute(select(Tender).where(Tender.updated_at >= since).order_by(Tender.updated_at.asc(), Tender.id.asc()))
		.scalars()
		.all()
	)

	total_created = 0
	for tender in tenders:
		total_created += match_tender(session=session, tender=tender)

	return total_created


def _build_tender_search_text(tender: Tender) -> str:
	"""Build a raw searchable text string from a tender."""
	parts = [
		tender.title,
		tender.issuing_entity,
		tender.category,
		tender.ai_summary,
		tender.tender_ref,
	]
	normalized_parts = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
	return ' '.join(normalized_parts)


def _extract_matched_keywords(
	*,
	search_token_set: set[str],
	keywords: list[str],
) -> list[str]:
	"""
	Return unique matched keywords in stable user-provided order.

	Matching behavior:
	    - Arabic/English aware via shared multilingual normalization
	    - token-based rather than raw substring-based
	    - all normalized keyword tokens must be present in the tender token set
	"""
	matched_keywords: list[str] = []
	seen: set[str] = set()

	for keyword in keywords:
		keyword_snapshot = build_multilingual_snapshot(keyword)
		collapsed_keyword = keyword_snapshot.collapsed

		if not collapsed_keyword:
			continue

		if collapsed_keyword in seen:
			continue

		if not keyword_snapshot.tokens:
			continue

		if not _all_keyword_tokens_present(
			search_token_set=search_token_set,
			keyword_tokens=keyword_snapshot.tokens,
		):
			continue

		seen.add(collapsed_keyword)
		matched_keywords.append(keyword.strip())

	return matched_keywords


def _all_keyword_tokens_present(
	*,
	search_token_set: set[str],
	keyword_tokens: tuple[str, ...],
) -> bool:
	"""Return whether all normalized keyword tokens are present in the tender."""
	return all(token in search_token_set for token in keyword_tokens)


def _profile_allows_tender_scope(
	*,
	profile: KeywordProfile,
	tender: Tender,
	source: Source,
) -> bool:
	"""Apply deterministic country and industry filters before keyword matching."""
	if not _country_scope_allows_profile(profile=profile, source=source):
		return False

	if not _industry_scope_allows_profile(profile=profile, tender=tender):
		return False

	return True


def _country_scope_allows_profile(*, profile: KeywordProfile, source: Source) -> bool:
	"""Return whether the source country is within the profile's allowed countries."""
	allowed_country_codes = list(profile.country_codes or [])
	if not allowed_country_codes:
		return True

	return source.country_code in allowed_country_codes


def _industry_scope_allows_profile(*, profile: KeywordProfile, tender: Tender) -> bool:
	"""Return whether the tender industries intersect the profile's allowed industries."""
	allowed_industry_codes = list(profile.industry_codes or [])
	if not allowed_industry_codes:
		return True

	tender_industry_codes = set(tender.industry_codes or [])
	if not tender_industry_codes:
		return False

	return any(industry_code in tender_industry_codes for industry_code in allowed_industry_codes)


def _build_matched_country_codes(*, profile: KeywordProfile, source: Source) -> list[str]:
	"""Persist the specific country scope evidence that allowed this match."""
	allowed_country_codes = list(profile.country_codes or [])
	if not allowed_country_codes:
		return []

	return [source.country_code]


def _build_matched_industry_codes(*, profile: KeywordProfile, tender: Tender) -> list[str]:
	"""Persist the specific normalized industries that allowed this match."""
	allowed_industry_codes = list(profile.industry_codes or [])
	if not allowed_industry_codes:
		return []

	tender_industry_codes = set(tender.industry_codes or [])
	return [industry_code for industry_code in allowed_industry_codes if industry_code in tender_industry_codes]
