from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user
from src.api.services.keyword_profile_service import (
    build_keyword_profile_response,
    get_keyword_profile_response,
    upsert_keyword_profile,
)
from src.db.models.user import User
from src.db.session import get_db_session
from src.shared.schemas.keyword_profile import (
    KeywordProfileResponse,
    KeywordProfileUpsertRequest,
)

router = APIRouter(tags=["keyword-profile"])


@router.get(
    "/me/keyword-profile",
    response_model=KeywordProfileResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_keyword_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> KeywordProfileResponse:
    """Return the current user's keyword profile."""
    return get_keyword_profile_response(
        session=session,
        user_id=current_user.id,
    )


@router.put(
    "/me/keyword-profile",
    response_model=KeywordProfileResponse,
    status_code=status.HTTP_200_OK,
)
def put_my_keyword_profile(
    payload: KeywordProfileUpsertRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> KeywordProfileResponse:
    """Create or replace the current user's keyword profile."""
    try:
        profile = upsert_keyword_profile(
            session=session,
            user_id=current_user.id,
            payload=payload,
        )
        session.commit()
        session.refresh(profile)
        return build_keyword_profile_response(profile)
    except Exception:
        session.rollback()
        raise
