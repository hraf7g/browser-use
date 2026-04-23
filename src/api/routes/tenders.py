from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user
from src.api.services.tender_details_service import (
    TenderDetailsNotFoundError,
    get_tender_details,
)
from src.api.services.tender_service import list_tenders
from src.db.models.user import User
from src.db.session import get_db_session
from src.shared.schemas.tender import TenderListQueryParams, TenderListResponse
from src.shared.schemas.tender_details import TenderDetailsResponse

router = APIRouter(tags=["tenders"])
_SOURCE_IDS_ADAPTER = TypeAdapter(list[UUID])


def _raise_query_validation_error(
    exc: ValidationError,
    *,
    field_name: str | None = None,
) -> None:
    normalized_errors: list[dict[str, object]] = []
    for error in exc.errors():
        raw_loc = error.get("loc", ())
        if isinstance(raw_loc, tuple):
            loc = raw_loc
        elif isinstance(raw_loc, list):
            loc = tuple(raw_loc)
        else:
            loc = (raw_loc,)

        if field_name is not None:
            loc = ("query", field_name, *loc)
        elif not loc or loc[0] != "query":
            loc = ("query", *loc)

        normalized_errors.append(
            {
                **error,
                "loc": loc,
            }
        )

    raise RequestValidationError(normalized_errors) from exc


def _parse_source_ids(source_ids: str | None) -> list[UUID]:
    if not source_ids:
        return []

    raw_source_ids = [item.strip() for item in source_ids.split(",") if item.strip()]
    if not raw_source_ids:
        return []

    try:
        return _SOURCE_IDS_ADAPTER.validate_python(raw_source_ids)
    except ValidationError as exc:
        _raise_query_validation_error(exc, field_name="source_ids")


@router.get(
    "/tenders",
    response_model=TenderListResponse,
    status_code=status.HTTP_200_OK,
)
def get_tenders(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    source_id: Annotated[UUID | None, Query()] = None,
    source_ids: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
    match_only: Annotated[bool, Query()] = False,
    new_only: Annotated[bool, Query()] = False,
    closing_soon: Annotated[bool, Query()] = False,
    sort: Annotated[str, Query()] = "relevance",
) -> TenderListResponse:
    """Return the authenticated user's paginated tenders list view."""
    parsed_source_ids = _parse_source_ids(source_ids)

    try:
        params = TenderListQueryParams(
            page=page,
            limit=limit,
            source_id=source_id,
            source_ids=parsed_source_ids,
            search=search,
            match_only=match_only,
            new_only=new_only,
            closing_soon=closing_soon,
            sort=sort,
        )
    except ValidationError as exc:
        _raise_query_validation_error(exc)

    return list_tenders(
        session=session,
        user_id=current_user.id,
        params=params,
    )


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
