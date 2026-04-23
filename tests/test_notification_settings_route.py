from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.dependencies.auth import get_current_user
from src.db.session import get_db_session
from src.notifications.notification_preference_service import (
	NotificationPreferenceValidationError,
)


def _fake_user():
	return SimpleNamespace(
		id=UUID('00000000-0000-0000-0000-000000000701'),
		email='notifications@example.com',
		is_active=True,
		is_operator=False,
	)


def test_put_notification_preferences_returns_422_for_domain_validation_error(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	app = create_app()
	calls: list[str] = []

	class FakeSession:
		def commit(self) -> None:
			calls.append('commit')

		def rollback(self) -> None:
			calls.append('rollback')

	app.dependency_overrides[get_db_session] = lambda: FakeSession()
	app.dependency_overrides[get_current_user] = _fake_user
	monkeypatch.setattr(
		'src.api.routes.notification_settings.update_notification_preference',
		lambda *, session, user_id, payload: (_ for _ in ()).throw(
			NotificationPreferenceValidationError('email_enabled must not be null')
		),
	)

	client = TestClient(app, raise_server_exceptions=False)
	response = client.put(
		'/me/notification-preferences',
		json={'email_enabled': None},
	)

	assert response.status_code == 422
	assert response.json() == {'detail': 'email_enabled must not be null'}
	assert calls == ['rollback']


def test_get_notification_deliveries_passes_validated_pagination(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	app = create_app()
	app.dependency_overrides[get_db_session] = lambda: object()
	app.dependency_overrides[get_current_user] = _fake_user
	captured: dict[str, object] = {}

	monkeypatch.setattr(
		'src.api.routes.notification_settings.list_notification_delivery_history',
		lambda *, session, user_id, page, limit: captured.update(
			{
				'user_id': user_id,
				'page': page,
				'limit': limit,
			}
		)
		or {
			'page': page,
			'limit': limit,
			'total': 0,
			'items': [],
		},
	)

	client = TestClient(app)
	response = client.get('/me/notification-deliveries', params={'page': 2, 'limit': 50})

	assert response.status_code == 200
	assert captured == {
		'user_id': _fake_user().id,
		'page': 2,
		'limit': 50,
	}


def test_get_notification_deliveries_rejects_invalid_page_with_422() -> None:
	app = create_app()
	app.dependency_overrides[get_db_session] = lambda: object()
	app.dependency_overrides[get_current_user] = _fake_user

	client = TestClient(app, raise_server_exceptions=False)
	response = client.get('/me/notification-deliveries', params={'page': 0})

	assert response.status_code == 422
