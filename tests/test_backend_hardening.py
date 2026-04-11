from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.responses import Response
from fastapi.testclient import TestClient
from pydantic import ValidationError

import src.api.dependencies.auth as auth_dependencies
import src.shared.config.settings as settings_module
from src.api.app import create_app
from src.api.routes import auth as auth_route
from src.db.session import get_db_session
from src.shared.config.settings import Settings
from src.shared.security.session import clear_access_token_cookie, set_access_token_cookie


@pytest.fixture(autouse=True)
def clear_settings_cache():
	settings_module.get_settings.cache_clear()
	yield
	settings_module.get_settings.cache_clear()


def _set_base_backend_env(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setenv('UTW_ENVIRONMENT', 'production')
	monkeypatch.setenv('UTW_DEBUG', 'false')
	monkeypatch.setenv(
		'UTW_DATABASE_URL',
		'postgresql+psycopg://postgres:postgres@localhost:5432/utw',
	)
	monkeypatch.setenv('UTW_AUTH_SECRET_KEY', 'super-secret-production-value')
	monkeypatch.setenv('UTW_AUTH_COOKIE_SECURE', 'true')
	monkeypatch.setenv('UTW_CORS_ALLOW_ORIGINS', 'https://app.example.com')


def test_production_settings_accept_explicit_safe_config(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_set_base_backend_env(monkeypatch)

	settings = Settings()

	assert settings.environment == 'production'
	assert settings.auth_cookie_secure is True
	assert settings.auth_cookie_path == '/'
	assert settings.auth_cookie_domain is None
	assert settings.cors_allow_origins_list == ['https://app.example.com']


def test_production_settings_reject_invalid_cookie_path(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_set_base_backend_env(monkeypatch)
	monkeypatch.setenv('UTW_AUTH_COOKIE_PATH', 'invalid-path')

	with pytest.raises(ValidationError):
		Settings()


def test_access_token_cookie_uses_configured_path_and_domain(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_set_base_backend_env(monkeypatch)
	monkeypatch.setenv('UTW_AUTH_COOKIE_PATH', '/app')
	monkeypatch.setenv('UTW_AUTH_COOKIE_DOMAIN', 'example.com')

	response = Response()
	set_access_token_cookie(response, 'token-value')
	cookie_header = response.headers['set-cookie']

	assert 'utw_access_token=token-value' in cookie_header
	assert 'Domain=example.com' in cookie_header
	assert 'Path=/app' in cookie_header
	assert 'HttpOnly' in cookie_header
	assert 'Secure' in cookie_header
	assert 'SameSite=lax' in cookie_header


def test_clear_access_token_cookie_uses_same_attributes(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_set_base_backend_env(monkeypatch)
	monkeypatch.setenv('UTW_AUTH_COOKIE_PATH', '/app')
	monkeypatch.setenv('UTW_AUTH_COOKIE_DOMAIN', 'example.com')

	response = Response()
	clear_access_token_cookie(response)
	cookie_header = response.headers['set-cookie']

	assert 'Domain=example.com' in cookie_header
	assert 'Path=/app' in cookie_header
	assert 'HttpOnly' in cookie_header
	assert 'Secure' in cookie_header
	assert 'SameSite=lax' in cookie_header


def test_login_response_is_cookie_only(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_set_base_backend_env(monkeypatch)
	app = create_app()

	fake_user = SimpleNamespace(
		id=UUID('00000000-0000-0000-0000-000000000111'),
		email='login-test@example.com',
		is_active=True,
	)

	class FakeSession:
		def commit(self) -> None:
			pass

		def refresh(self, user: object) -> None:
			pass

		def rollback(self) -> None:
			pass

	def override_session() -> FakeSession:
		return FakeSession()

	def fake_authenticate_user(*, session: object, payload: object) -> tuple[object, str]:
		return fake_user, 'server-only-token'

	monkeypatch.setattr(auth_route, 'authenticate_user', fake_authenticate_user)
	app.dependency_overrides[get_db_session] = override_session

	client = TestClient(app)
	response = client.post(
		'/auth/login',
		json={'email': 'login-test@example.com', 'password': 'StrongPass123!'},
	)

	assert response.status_code == 200
	assert response.json() == {
		'id': '00000000-0000-0000-0000-000000000111',
		'email': 'login-test@example.com',
		'is_active': True,
	}
	assert 'access_token' not in response.json()
	assert 'token_type' not in response.json()

	cookie_header = response.headers['set-cookie']
	assert 'utw_access_token=server-only-token' in cookie_header
	assert 'HttpOnly' in cookie_header


def test_signup_sets_cookie_and_me_uses_cookie_auth(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	_set_base_backend_env(monkeypatch)
	monkeypatch.setenv('UTW_ENVIRONMENT', 'development')
	monkeypatch.setenv('UTW_AUTH_COOKIE_SECURE', 'false')
	app = create_app()

	fake_user = SimpleNamespace(
		id=UUID('00000000-0000-0000-0000-000000000222'),
		email='signup-test@example.com',
		is_active=True,
	)
	seen_tokens: list[str] = []

	class FakeSession:
		def commit(self) -> None:
			pass

		def refresh(self, user: object) -> None:
			pass

		def rollback(self) -> None:
			pass

	def override_session() -> FakeSession:
		return FakeSession()

	def fake_register_user(*, session: object, payload: object) -> object:
		return fake_user

	def fake_create_access_token(*, user_id: object, email: str) -> str:
		return 'signup-cookie-token'

	def fake_decode_access_token(token: str) -> SimpleNamespace:
		seen_tokens.append(token)
		return SimpleNamespace(subject=fake_user.id)

	def fake_get_user_by_id(session: object, user_id: UUID) -> object:
		return fake_user

	monkeypatch.setattr(auth_route, 'register_user', fake_register_user)
	monkeypatch.setattr(auth_route, 'create_access_token', fake_create_access_token)
	monkeypatch.setattr(auth_dependencies, 'decode_access_token', fake_decode_access_token)
	monkeypatch.setattr(auth_dependencies, 'get_user_by_id', fake_get_user_by_id)
	app.dependency_overrides[get_db_session] = override_session

	client = TestClient(app)
	signup_response = client.post(
		'/auth/signup',
		json={'email': 'signup-test@example.com', 'password': 'StrongPass123!'},
	)

	assert signup_response.status_code == 201
	assert signup_response.json() == {
		'id': '00000000-0000-0000-0000-000000000222',
		'email': 'signup-test@example.com',
		'is_active': True,
	}
	assert 'utw_access_token=signup-cookie-token' in signup_response.headers['set-cookie']

	me_response = client.get('/me')

	assert me_response.status_code == 200
	assert me_response.json() == {
		'id': '00000000-0000-0000-0000-000000000222',
		'email': 'signup-test@example.com',
		'is_active': True,
	}
	assert seen_tokens == ['signup-cookie-token']
