from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user
from src.db.models.user import User
from src.db.session import get_db_session
from src.notifications.notification_history_service import (
    list_notification_delivery_history,
)
from src.notifications.notification_preference_service import (
    NotificationPreferenceValidationError,
    get_or_create_notification_preference,
    update_notification_preference,
)
from src.shared.schemas.notification_history import (
    NotificationDeliveryHistoryResponse,
)
from src.shared.schemas.notification_preference import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdateRequest,
)

router = APIRouter(tags=["notification-settings"])


@router.get(
    "/me/notification-preferences",
    response_model=NotificationPreferenceResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_notification_preferences(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> NotificationPreferenceResponse:
    """
    Return the current user's notification preferences.

    Notes:
        - Creates and persists a default preference row when absent.
    """
    try:
        response = get_or_create_notification_preference(
            session=session,
            user_id=current_user.id,
        )
        session.commit()
        return response
    except Exception:
        session.rollback()
        raise


@router.put(
    "/me/notification-preferences",
    response_model=NotificationPreferenceResponse,
    status_code=status.HTTP_200_OK,
)
def put_my_notification_preferences(
    payload: NotificationPreferenceUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> NotificationPreferenceResponse:
    """Update the current user's notification preferences."""
    try:
        response = update_notification_preference(
            session=session,
            user_id=current_user.id,
            payload=payload,
        )
        session.commit()
        return response
    except NotificationPreferenceValidationError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception:
        session.rollback()
        raise


@router.get(
    "/me/notification-deliveries",
    response_model=NotificationDeliveryHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_notification_deliveries(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> NotificationDeliveryHistoryResponse:
    """Return the current user's paginated notification delivery history."""
    return list_notification_delivery_history(
        session=session,
        user_id=current_user.id,
        page=page,
        limit=limit,
    )
