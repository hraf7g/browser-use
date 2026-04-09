from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.dependencies.auth import get_current_user
from src.api.services.auth_service import build_user_summary
from src.db.models.user import User
from src.shared.schemas.auth import UserSummary

router = APIRouter(tags=["me"])


@router.get(
    "/me",
    response_model=UserSummary,
    status_code=status.HTTP_200_OK,
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserSummary:
    """Return the currently authenticated user."""
    return build_user_summary(current_user)
