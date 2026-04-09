from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.user import User
from src.shared.schemas.auth import (
    LoginRequest,
    SignupRequest,
    UserSummary,
)
from src.shared.security.passwords import PasswordHashError, hash_password, verify_password
from src.shared.security.tokens import create_access_token


class AuthServiceError(ValueError):
    """Base class for authentication service errors."""


class EmailAlreadyExistsError(AuthServiceError):
    """Raised when a signup attempt uses an existing email address."""


class InvalidCredentialsError(AuthServiceError):
    """Raised when login credentials are invalid."""


class InactiveUserError(AuthServiceError):
    """Raised when an inactive user attempts to authenticate."""


class UserNotFoundError(AuthServiceError):
    """Raised when a requested user cannot be found."""


def register_user(session: Session, payload: SignupRequest) -> User:
    """
    Register a new user account.

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
    """
    existing_user = session.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if existing_user is not None:
        raise EmailAlreadyExistsError("an account with this email already exists")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    session.add(user)
    session.flush()

    return user


def authenticate_user(
    session: Session,
    payload: LoginRequest,
) -> tuple[User, str]:
    """
    Authenticate a user and issue an access token.

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
    """
    user = session.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if user is None:
        raise InvalidCredentialsError("invalid email or password")

    if not user.is_active:
        raise InactiveUserError("user account is inactive")

    try:
        password_is_valid = verify_password(
            payload.password,
            user.password_hash,
        )
    except PasswordHashError as exc:
        raise InvalidCredentialsError("invalid email or password") from exc

    if not password_is_valid:
        raise InvalidCredentialsError("invalid email or password")

    user.last_login_at = datetime.now(timezone.utc)
    session.flush()

    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
    )
    return user, access_token


def get_user_by_id(session: Session, user_id: UUID) -> User:
    """Fetch a user by id or raise a domain error if not found."""
    user = session.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"user '{user_id}' was not found")
    return user


def build_user_summary(user: User) -> UserSummary:
    """Build a safe user summary payload from a user model."""
    return UserSummary(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
    )
