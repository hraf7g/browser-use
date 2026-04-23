from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.keyword_profile import KeywordProfile
from src.shared.industry_taxonomy import classify_profile_industry_codes
from src.shared.schemas.keyword_profile import (
	KeywordProfileResponse,
	KeywordProfileUpsertRequest,
)


def get_keyword_profile_response(
	session: Session,
	*,
	user_id: UUID,
) -> KeywordProfileResponse:
	"""
	Return the current user's keyword profile response.

	If no profile exists yet, return a safe default payload.
	"""
	profile = session.execute(select(KeywordProfile).where(KeywordProfile.user_id == user_id)).scalar_one_or_none()

	if profile is None:
		return KeywordProfileResponse(
			keywords=[],
			alert_enabled=True,
			country_codes=[],
			industry_codes=[],
			industry_label=None,
		)

	return build_keyword_profile_response(profile)


def upsert_keyword_profile(
	session: Session,
	*,
	user_id: UUID,
	payload: KeywordProfileUpsertRequest,
) -> KeywordProfile:
	"""
	Create or update the current user's keyword profile.

	Notes:
	    - This function does not commit the transaction.
	    - The caller owns transaction boundaries.
	"""
	profile = session.execute(select(KeywordProfile).where(KeywordProfile.user_id == user_id)).scalar_one_or_none()
	normalized_industry_codes = _resolve_profile_industry_codes(payload=payload)

	if profile is None:
		profile = KeywordProfile(
			user_id=user_id,
			keywords=list(payload.keywords),
			alert_enabled=payload.alert_enabled,
			country_codes=list(payload.country_codes),
			industry_codes=normalized_industry_codes,
			industry_label=payload.industry_label,
		)
		session.add(profile)
		session.flush()
		return profile

	profile.keywords = list(payload.keywords)
	profile.alert_enabled = payload.alert_enabled
	profile.country_codes = list(payload.country_codes)
	profile.industry_codes = normalized_industry_codes
	profile.industry_label = payload.industry_label
	session.flush()

	return profile


def build_keyword_profile_response(
	profile: KeywordProfile,
) -> KeywordProfileResponse:
	"""Build a safe keyword profile response from the model."""
	return KeywordProfileResponse(
		keywords=list(profile.keywords),
		alert_enabled=profile.alert_enabled,
		country_codes=list(profile.country_codes or []),
		industry_codes=list(profile.industry_codes or []),
		industry_label=profile.industry_label,
	)


def _resolve_profile_industry_codes(*, payload: KeywordProfileUpsertRequest) -> list[str]:
	"""Preserve normalized industry codes even when callers still send only a display label."""
	if payload.industry_codes:
		return list(payload.industry_codes)

	return classify_profile_industry_codes(
		industry_label=payload.industry_label,
		keywords=list(payload.keywords),
	)
