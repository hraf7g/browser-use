from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from src.shared.config.settings import get_settings


class TokenError(ValueError):
    """Raised when token creation or validation fails."""


@dataclass(frozen=True)
class AccessTokenClaims:
    """Validated access token claims used by the application."""

    subject: UUID
    email: str
    issued_at: datetime
    expires_at: datetime
    issuer: str
    audience: str


def create_access_token(*, user_id: UUID, email: str) -> str:
    """Create a signed access token for an authenticated user."""
    settings = get_settings()
    secret_key = settings.auth_secret_key.get_secret_value().strip()
    if not secret_key:
        raise TokenError("auth_secret_key must not be empty")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.auth_access_token_ttl_minutes)

    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": settings.auth_issuer,
        "aud": settings.auth_audience,
    }

    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(token: str) -> AccessTokenClaims:
    """Decode and validate a signed access token."""
    if not isinstance(token, str):
        raise TypeError("token must be a string")

    normalized_token = token.strip()
    if not normalized_token:
        raise TokenError("token must not be empty")

    settings = get_settings()
    secret_key = settings.auth_secret_key.get_secret_value().strip()
    if not secret_key:
        raise TokenError("auth_secret_key must not be empty")

    try:
        payload = jwt.decode(
            normalized_token,
            secret_key,
            algorithms=["HS256"],
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
            options={
                "require": ["sub", "email", "iat", "exp", "iss", "aud"],
            },
        )
    except InvalidTokenError as exc:
        raise TokenError("invalid access token") from exc

    try:
        subject = UUID(str(payload["sub"]))
        email = str(payload["email"]).strip()
        issued_at = datetime.fromtimestamp(int(payload["iat"]), tz=timezone.utc)
        expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
        issuer = str(payload["iss"])
        audience = str(payload["aud"])
    except Exception as exc:
        raise TokenError("access token claims are malformed") from exc

    if not email:
        raise TokenError("access token email claim must not be empty")

    return AccessTokenClaims(
        subject=subject,
        email=email,
        issued_at=issued_at,
        expires_at=expires_at,
        issuer=issuer,
        audience=audience,
    )
