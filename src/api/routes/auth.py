from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.api.services.auth_service import (
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    authenticate_user,
    build_user_summary,
    register_user,
)
from src.db.session import get_db_session
from src.shared.security.session import clear_access_token_cookie, set_access_token_cookie
from src.shared.security.tokens import create_access_token
from src.shared.schemas.auth import (
    LoginRequest,
    SignupRequest,
    UserSummary,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=UserSummary,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    payload: SignupRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
) -> UserSummary:
    """Register a new user account."""
    try:
        user = register_user(session=session, payload=payload)
        session.commit()
        session.refresh(user)
        access_token = create_access_token(user_id=user.id, email=user.email)
        set_access_token_cookie(response, access_token)
        return build_user_summary(user)
    except EmailAlreadyExistsError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except Exception:
        session.rollback()
        raise


@router.post(
    "/login",
    response_model=UserSummary,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
) -> UserSummary:
    """Authenticate a user and set the session cookie."""
    try:
        user, access_token = authenticate_user(session=session, payload=payload)
        session.commit()
        session.refresh(user)
        set_access_token_cookie(response, access_token)
        return build_user_summary(user)
    except (InvalidCredentialsError, InactiveUserError) as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception:
        session.rollback()
        raise


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(response: Response) -> None:
    """Clear the current auth session cookie."""
    clear_access_token_cookie(response)
