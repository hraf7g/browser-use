from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.keyword_profile import KeywordProfile
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
    profile = session.execute(
        select(KeywordProfile).where(KeywordProfile.user_id == user_id)
    ).scalar_one_or_none()

    if profile is None:
        return KeywordProfileResponse(
            keywords=[],
            alert_enabled=True,
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
    profile = session.execute(
        select(KeywordProfile).where(KeywordProfile.user_id == user_id)
    ).scalar_one_or_none()

    if profile is None:
        profile = KeywordProfile(
            user_id=user_id,
            keywords=list(payload.keywords),
            alert_enabled=payload.alert_enabled,
            industry_label=payload.industry_label,
        )
        session.add(profile)
        session.flush()
        return profile

    profile.keywords = list(payload.keywords)
    profile.alert_enabled = payload.alert_enabled
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
        industry_label=profile.industry_label,
    )
