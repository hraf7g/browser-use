from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Header, HTTPException, status

from src.shared.config.settings import get_settings

OPERATOR_API_KEY_HEADER_NAME = "X-Operator-Key"


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
