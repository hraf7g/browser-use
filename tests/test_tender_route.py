from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.dependencies.auth import get_current_user
from src.db.session import get_db_session


def _fake_user():
	return SimpleNamespace(
		id=UUID('00000000-0000-0000-0000-000000000501'),
		email='tender-user@example.com',
		is_active=True,
		is_operator=False,
	)


def test_get_tenders_rejects_invalid_source_ids_with_422() -> None:
	app = create_app()
	app.dependency_overrides[get_db_session] = lambda: object()
	app.dependency_overrides[get_current_user] = _fake_user

	client = TestClient(app, raise_server_exceptions=False)
	response = client.get('/tenders', params={'source_ids': 'not-a-uuid'})

	assert response.status_code == 422
	assert response.json()['detail'][0]['loc'][:2] == ['query', 'source_ids']


def test_get_tenders_rejects_invalid_sort_with_422() -> None:
	app = create_app()
	app.dependency_overrides[get_db_session] = lambda: object()
	app.dependency_overrides[get_current_user] = _fake_user

	client = TestClient(app, raise_server_exceptions=False)
	response = client.get('/tenders', params={'sort': 'bogus'})

	assert response.status_code == 422
	assert response.json()['detail'][0]['loc'] == ['query', 'sort']


def test_get_tenders_accepts_comma_separated_source_ids(monkeypatch: pytest.MonkeyPatch) -> None:
	app = create_app()
	app.dependency_overrides[get_db_session] = lambda: object()
	app.dependency_overrides[get_current_user] = _fake_user

	source_id_1 = UUID('00000000-0000-0000-0000-000000000111')
	source_id_2 = UUID('00000000-0000-0000-0000-000000000222')
	captured: dict[str, object] = {}

	monkeypatch.setattr(
		'src.api.routes.tenders.list_tenders',
		lambda *, session, user_id, params: captured.update(
			{
				'session': session,
				'user_id': user_id,
				'source_ids': params.source_ids,
			}
		)
		or {
			'items': [],
			'available_sources': [],
			'total': 0,
			'page': params.page,
			'limit': params.limit,
		},
	)

	client = TestClient(app)
	response = client.get('/tenders', params={'source_ids': f'{source_id_1},{source_id_2}'})

	assert response.status_code == 200
	assert captured['user_id'] == _fake_user().id
	assert captured['source_ids'] == [source_id_1, source_id_2]
