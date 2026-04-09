from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user
from src.api.services.tender_service import list_tenders
from src.api.services.tender_details_service import (
    TenderDetailsNotFoundError,
    get_tender_details,
)
from src.db.models.user import User
from src.db.session import get_db_session
from src.shared.schemas.tender import TenderListQueryParams, TenderListResponse
from src.shared.schemas.tender_details import TenderDetailsResponse

router = APIRouter(tags=["tenders"])


@router.get(
    "/tenders",
    response_model=TenderListResponse,
    status_code=status.HTTP_200_OK,
)
def get_tenders(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    source_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None, max_length=255),
) -> TenderListResponse:
    """Return the authenticated user's paginated tenders list view."""
    _ = current_user

    params = TenderListQueryParams(
        page=page,
        limit=limit,
        source_id=source_id,
        search=search,
    )
    return list_tenders(session=session, params=params)


@router.get(
    "/tenders/{tender_id}",
    response_model=TenderDetailsResponse,
    status_code=status.HTTP_200_OK,
)
def get_tender(
    tender_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
) -> TenderDetailsResponse:
    """Return the authenticated user's view of one tender."""
    try:
        return get_tender_details(
            session=session,
            user_id=current_user.id,
            tender_id=tender_id,
        )
    except TenderDetailsNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
