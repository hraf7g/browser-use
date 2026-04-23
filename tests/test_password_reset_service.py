from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.api.services.password_reset_service import (
    InvalidPasswordResetTokenError,
    request_password_reset,
    reset_password,
)
from src.shared.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest


class _ScalarOneOrNoneResult:
    def __init__(self, value: object | None):
        self._value = value

    def scalar_one_or_none(self) -> object | None:
        return self._value


class _ScalarsResult:
    def __init__(self, values: list[object]):
        self._values = values

    def scalars(self) -> "_ScalarsResult":
        return self

    def all(self) -> list[object]:
        return list(self._values)


class FakeSession:
    def __init__(self, *, execute_results: list[object], users_by_id: dict[object, object] | None = None):
        self._execute_results = list(execute_results)
        self._users_by_id = users_by_id or {}
        self.added: list[object] = []
        self.flush_calls = 0

    def execute(self, statement: object) -> object:
        if not self._execute_results:
            raise AssertionError('unexpected execute() call')
        return self._execute_results.pop(0)

    def add(self, value: object) -> None:
        self.added.append(value)

    def flush(self) -> None:
        self.flush_calls += 1

    def get(self, model: object, key: object) -> object | None:
        return self._users_by_id.get(key)


def test_request_password_reset_is_generic_for_missing_user() -> None:
    session = FakeSession(
        execute_results=[
            _ScalarOneOrNoneResult(None),
        ]
    )

    result = request_password_reset(
        session,
        payload=ForgotPasswordRequest(email='missing@example.com'),
    )

    assert result.delivered is False
    assert result.delivery_channel == 'dev_outbox'
    assert session.added == []


def test_reset_password_updates_password_and_invalidates_token(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()
    reset_token = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        token_hash='hashed-token',
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        used_at=None,
    )
    second_token = SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        token_hash='second-token',
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        used_at=None,
    )
    user = SimpleNamespace(
        id=user_id,
        email='user@example.com',
        is_active=True,
        password_hash='old-hash',
    )
    session = FakeSession(
        execute_results=[
            _ScalarOneOrNoneResult(reset_token),
            _ScalarsResult([reset_token, second_token]),
        ],
        users_by_id={user_id: user},
    )

    monkeypatch.setattr(
        'src.api.services.password_reset_service.hash_password_reset_token',
        lambda token: 'hashed-token',
    )
    monkeypatch.setattr(
        'src.api.services.password_reset_service.hash_password',
        lambda password: f'hashed::{password}',
    )

    returned_user_id = reset_password(
        session,
        payload=ResetPasswordRequest(token='raw-token', password='NewPassword123!'),
    )

    assert returned_user_id == user_id
    assert user.password_hash == 'hashed::NewPassword123!'
    assert reset_token.used_at is not None
    assert second_token.used_at is not None


def test_reset_password_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_token = SimpleNamespace(
        id=uuid4(),
        user_id=uuid4(),
        token_hash='hashed-token',
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        used_at=None,
    )
    session = FakeSession(
        execute_results=[
            _ScalarOneOrNoneResult(reset_token),
        ]
    )

    monkeypatch.setattr(
        'src.api.services.password_reset_service.hash_password_reset_token',
        lambda token: 'hashed-token',
    )

    with pytest.raises(InvalidPasswordResetTokenError):
        reset_password(
            session,
            payload=ResetPasswordRequest(token='expired-token', password='AnotherPassword123!'),
        )
