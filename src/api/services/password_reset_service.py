from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.password_reset_token import PasswordResetToken
from src.db.models.user import User
from src.email.backend import get_email_delivery_backend_name
from src.shared.config.settings import get_settings
from src.shared.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest
from src.shared.security.password_reset_tokens import (
    generate_password_reset_token,
    hash_password_reset_token,
)
from src.shared.security.passwords import hash_password


class InvalidPasswordResetTokenError(ValueError):
    """Raised when a password reset token is invalid or expired."""


@dataclass(frozen=True)
class ForgotPasswordDispatchResult:
    """Metadata describing the accepted forgot-password request."""

    delivery_channel: str
    delivered: bool
    recipient_email: str | None = None
    reset_token: str | None = None


def request_password_reset(
    session: Session,
    *,
    payload: ForgotPasswordRequest,
) -> ForgotPasswordDispatchResult:
    """
    Create a one-time password reset token when the user exists and is active.

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
        - The return shape is intentionally generic to avoid leaking account existence.
    """
    settings = get_settings()
    user = session.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()
    delivery_channel = get_email_delivery_backend_name(settings)

    if user is None or not user.is_active:
        return ForgotPasswordDispatchResult(
            delivery_channel=delivery_channel,
            delivered=False,
        )

    _revoke_active_tokens_for_user(session, user_id=user.id)

    raw_token = generate_password_reset_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.password_reset_token_ttl_minutes
    )
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_password_reset_token(raw_token),
        expires_at=expires_at,
        used_at=None,
    )
    session.add(reset_token)
    session.flush()

    return ForgotPasswordDispatchResult(
        delivery_channel=delivery_channel,
        delivered=True,
        recipient_email=user.email,
        reset_token=raw_token,
    )


def reset_password(
    session: Session,
    *,
    payload: ResetPasswordRequest,
) -> UUID:
    """
    Reset a user's password using a valid one-time reset token.

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
        - The matched token and all other active tokens for the user are invalidated.
    """
    now = datetime.now(timezone.utc)
    token_hash = hash_password_reset_token(payload.token)

    reset_token = session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash
        )
    ).scalar_one_or_none()

    if (
        reset_token is None
        or reset_token.used_at is not None
        or reset_token.expires_at <= now
    ):
        raise InvalidPasswordResetTokenError('invalid or expired password reset token')

    user = session.get(User, reset_token.user_id)
    if user is None or not user.is_active:
        raise InvalidPasswordResetTokenError('invalid or expired password reset token')

    user.password_hash = hash_password(payload.password)
    reset_token.used_at = now
    _revoke_active_tokens_for_user(
        session,
        user_id=user.id,
        revoked_at=now,
        exclude_token_id=reset_token.id,
    )
    session.flush()

    return user.id


def _revoke_active_tokens_for_user(
    session: Session,
    *,
    user_id: UUID,
    revoked_at: datetime | None = None,
    exclude_token_id: UUID | None = None,
) -> None:
    """Mark all outstanding password reset tokens for a user as used."""
    now = revoked_at or datetime.now(timezone.utc)
    active_tokens = session.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.used_at.is_(None),
        )
    ).scalars().all()

    for token in active_tokens:
        if exclude_token_id is not None and token.id == exclude_token_id:
            continue
        token.used_at = now

    session.flush()
