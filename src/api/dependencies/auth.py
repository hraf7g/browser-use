from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.api.services.auth_service import UserNotFoundError, get_user_by_id
from src.db.models.user import User
from src.db.session import get_db_session
from src.shared.config.settings import get_settings
from src.shared.logging.logger import get_logger
from src.shared.security.session import get_access_token_from_cookie
from src.shared.security.tokens import (
    AccessTokenClaims,
    TokenError,
    decode_access_token,
)

_bearer_scheme = HTTPBearer(auto_error=False)
logger = get_logger(__name__)


def _unauthorized(detail: str = "authentication required") -> HTTPException:
    """Create a consistent unauthorized HTTP exception."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _token_error_category(exc: TokenError) -> str:
    """Map a token error to a stable, non-sensitive category."""
    message = str(exc).lower()

    if "auth_secret_key must not be empty" in message:
        return "secret_missing"
    if "token must not be empty" in message:
        return "missing_token"
    if "invalid access token" in message:
        return "invalid_token"
    if "access token claims are malformed" in message:
        return "malformed_claims"
    if "access token email claim must not be empty" in message:
        return "empty_email_claim"
    return "token_error"


def get_bearer_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    request: Request,
) -> str:
    """Extract the current auth token from the request or raise 401."""
    cookie_name = get_settings().auth_cookie_name
    cookie_value = request.cookies.get(cookie_name)
    cookie_present = cookie_value is not None and bool(cookie_value.strip())

    if credentials is not None:
        token = credentials.credentials.strip()
        if token:
            logger.info(
                "auth_request_token_source source=authorization_header cookie_present=%s cookie_name=%s",
                cookie_present,
                cookie_name,
            )
            return token

    token = get_access_token_from_cookie(request)
    if token is None:
        logger.info(
            "auth_request_token_source source=missing cookie_present=%s cookie_name=%s",
            cookie_present,
            cookie_name,
        )
        raise _unauthorized()

    logger.info(
        "auth_request_token_source source=cookie cookie_present=%s cookie_name=%s",
        cookie_present,
        cookie_name,
    )
    return token


def get_current_token_claims(
    token: Annotated[str, Depends(get_bearer_token)],
) -> AccessTokenClaims:
    """Decode and validate the current bearer token."""
    try:
        claims = decode_access_token(token)
        logger.info("auth_token_decode_result outcome=success")
        return claims
    except TokenError as exc:
        logger.warning(
            "auth_token_decode_result outcome=failure category=%s",
            _token_error_category(exc),
        )
        raise _unauthorized("invalid authentication token") from exc


def get_current_user(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[Session, Depends(get_db_session)],
) -> User:
    """Resolve the current authenticated user from token claims."""
    try:
        user = get_user_by_id(session, claims.subject)
    except UserNotFoundError as exc:
        logger.warning("auth_current_user_lookup outcome=failure category=user_not_found")
        raise _unauthorized("invalid authentication token") from exc

    if not user.is_active:
        logger.warning("auth_current_user_lookup outcome=failure category=user_inactive")
        raise _unauthorized("user account is inactive")

    logger.info("auth_current_user_lookup outcome=success")
    return user


def get_current_user_optional(
    request: Request,
    session: Annotated[Session, Depends(get_db_session)],
) -> User | None:
    """Resolve the current user when a valid auth token is present, else return None."""
    try:
        token = get_bearer_token(None, request)
        claims = decode_access_token(token)
        user = get_user_by_id(session, claims.subject)
    except (HTTPException, TokenError, UserNotFoundError):
        return None

    if not user.is_active:
        return None

    return user
