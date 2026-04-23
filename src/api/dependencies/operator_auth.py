from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from src.api.dependencies.auth import get_current_user_optional
from src.db.models.user import User
from src.shared.config.settings import get_settings

OPERATOR_API_KEY_HEADER_NAME = "X-Operator-Key"


@dataclass(frozen=True)
class OperatorAccessContext:
    """Normalized operator-access identity used for audit logging."""

    access_path: str
    operator_user_id: str | None
    operator_email: str | None


def require_operator_api_key(
    x_operator_key: Annotated[
        str | None,
        Header(
            alias=OPERATOR_API_KEY_HEADER_NAME,
            convert_underscores=False,
        ),
    ] = None,
) -> None:
    """
    Enforce operator-only access using a static operator API key header.

    Security notes:
        - fails closed when operator_api_key is not configured
        - uses constant-time comparison
        - does not leak whether the presented key was close to correct
    """
    settings = get_settings()
    configured_key = settings.operator_api_key.get_secret_value().strip()

    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="operator access is not configured",
        )

    presented_key = (x_operator_key or "").strip()
    if not presented_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="operator authentication required",
        )

    if not hmac.compare_digest(presented_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid operator credentials",
        )


def require_operator_access(
    current_user: Annotated[User | None, Depends(get_current_user_optional)],
    x_operator_key: Annotated[
        str | None,
        Header(
            alias=OPERATOR_API_KEY_HEADER_NAME,
            convert_underscores=False,
        ),
    ] = None,
) -> OperatorAccessContext:
    """
    Enforce operator access using either an operator user session or the static API key.

    Security notes:
        - operator user sessions are the primary interactive access path
        - the static API key remains available for non-user automation
        - non-operator authenticated users are rejected even if a session is present
    """
    if current_user is not None:
        if current_user.is_operator:
            return OperatorAccessContext(
                access_path='operator_session',
                operator_user_id=str(current_user.id),
                operator_email=current_user.email,
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="operator role required",
        )

    require_operator_api_key(x_operator_key)
    return OperatorAccessContext(
        access_path='api_key',
        operator_user_id=None,
        operator_email=None,
    )
