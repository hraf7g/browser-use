from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user
from src.api.services.activity_overview_service import get_activity_overview
from src.db.models.user import User
from src.db.session import get_db_session
from src.shared.schemas.activity_overview import ActivityOverviewResponse

router = APIRouter(tags=['activity'])


@router.get(
    '/me/activity-overview',
    response_model=ActivityOverviewResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_activity_overview(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> ActivityOverviewResponse:
    """Return a safe activity and source-monitoring overview for the current user."""
    return get_activity_overview(session=session, user_id=current_user.id)
