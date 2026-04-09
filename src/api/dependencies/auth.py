from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.api.services.auth_service import UserNotFoundError, get_user_by_id
from src.db.models.user import User
from src.db.session import get_db_session
from src.shared.security.session import get_access_token_from_cookie
from src.shared.security.tokens import (
    AccessTokenClaims,
    TokenError,
    decode_access_token,
)

_bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "authentication required") -> HTTPException:
    """Create a consistent unauthorized HTTP exception."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    request: Request,
) -> str:
    """Extract the current auth token from the request or raise 401."""
    if credentials is not None:
        token = credentials.credentials.strip()
        if token:
            return token

    token = get_access_token_from_cookie(request)
    if token is None:
        raise _unauthorized()

    return token


def get_current_token_claims(
    token: Annotated[str, Depends(get_bearer_token)],
) -> AccessTokenClaims:
    """Decode and validate the current bearer token."""
    try:
        return decode_access_token(token)
    except TokenError as exc:
        raise _unauthorized("invalid authentication token") from exc


def get_current_user(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[Session, Depends(get_db_session)],
) -> User:
    """Resolve the current authenticated user from token claims."""
    try:
        user = get_user_by_id(session, claims.subject)
    except UserNotFoundError as exc:
        raise _unauthorized("invalid authentication token") from exc

    if not user.is_active:
        raise _unauthorized("user account is inactive")

    return user
