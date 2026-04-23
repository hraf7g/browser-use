from __future__ import annotations

import hashlib
import secrets

RESET_TOKEN_BYTES = 32


def generate_password_reset_token() -> str:
    """Generate a high-entropy password reset token suitable for URLs."""
    return secrets.token_urlsafe(RESET_TOKEN_BYTES)


def hash_password_reset_token(token: str) -> str:
    """Hash a reset token before persistence or lookup."""
    if not isinstance(token, str):
        raise TypeError('token must be a string')

    normalized = token.strip()
    if not normalized:
        raise ValueError('token must not be empty')

    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
