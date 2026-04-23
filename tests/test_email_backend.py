from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import src.shared.config.settings as settings_module
from src.api.services.password_reset_service import request_password_reset
from src.email.backend import send_email_message
from src.email.password_reset_email_service import dispatch_password_reset_email
from src.shared.schemas.auth import ForgotPasswordRequest
from src.shared.schemas.email import EmailMessage


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
	settings_module.get_settings.cache_clear()
	yield
	settings_module.get_settings.cache_clear()


def test_send_email_message_dev_outbox_writes_file(
	tmp_path: Path,
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setenv('UTW_EMAIL_DELIVERY_BACKEND', 'dev_outbox')
	result = send_email_message(
		EmailMessage(
			to='user@example.com',
			subject='Subject',
			body_text='Hello from tests',
		),
		outbox_dir=tmp_path,
	)

	assert result.provider == 'dev_outbox'
	assert result.output_path is not None
	assert result.output_path.exists()
	assert result.message_id
	assert 'user@example.com' in result.output_path.read_text(encoding='utf-8')


def test_send_email_message_ses_uses_expected_payload(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setenv('UTW_EMAIL_DELIVERY_BACKEND', 'ses')
	monkeypatch.setenv('UTW_EMAIL_SENDER', 'alerts@example.com')
	monkeypatch.setenv('UTW_EMAIL_REPLY_TO', 'support@example.com')
	monkeypatch.setenv('UTW_EMAIL_SES_CONFIGURATION_SET', 'prod-config')
	monkeypatch.setenv('UTW_EMAIL_SES_FROM_ARN', 'arn:aws:ses:us-east-1:123456789012:identity/example.com')
	monkeypatch.setenv('UTW_AWS_REGION', 'us-east-1')

	calls: list[tuple[str, str | None, dict[str, object]]] = []

	class FakeSesClient:
		def send_email(self, **kwargs: object) -> dict[str, str]:
			calls.append(('send_email', None, kwargs))
			return {'MessageId': 'ses-message-id'}

		def __repr__(self) -> str:  # pragma: no cover - debug fallback only
			return 'FakeSesClient()'

	def fake_boto3_client(service_name: str, region_name: str | None = None) -> FakeSesClient:
		calls.append(('client', region_name, {'service_name': service_name}))
		assert service_name == 'sesv2'
		return FakeSesClient()

	monkeypatch.setitem(__import__('sys').modules, 'boto3', SimpleNamespace(client=fake_boto3_client))

	result = send_email_message(
		EmailMessage(
			to='user@example.com',
			subject='Prod Subject',
			body_text='Prod Body',
		)
	)

	assert result.provider == 'ses'
	assert result.message_id == 'ses-message-id'
	assert result.output_path is None
	assert calls[0] == ('client', 'us-east-1', {'service_name': 'sesv2'})
	send_call = calls[1]
	assert send_call[0] == 'send_email'
	assert send_call[2] == {
		'FromEmailAddress': 'alerts@example.com',
		'Destination': {'ToAddresses': ['user@example.com']},
		'Content': {
			'Simple': {
				'Subject': {'Data': 'Prod Subject', 'Charset': 'UTF-8'},
				'Body': {'Text': {'Data': 'Prod Body', 'Charset': 'UTF-8'}},
			},
		},
		'ReplyToAddresses': ['support@example.com'],
		'ConfigurationSetName': 'prod-config',
		'FromEmailAddressIdentityArn': 'arn:aws:ses:us-east-1:123456789012:identity/example.com',
	}


def test_dispatch_password_reset_email_uses_configured_backend(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setattr(
		'src.email.password_reset_email_service.send_email_message',
		lambda message, outbox_dir: SimpleNamespace(
			message_id='provider-message-id',
			output_path=None,
			provider='ses',
		),
	)

	result = dispatch_password_reset_email(
		recipient_email='user@example.com',
		reset_token='abc123',
		frontend_base_url='https://app.example.com',
	)

	assert result.provider == 'ses'
	assert result.message_id == 'provider-message-id'
	assert result.output_path is None
	assert result.reset_url == 'https://app.example.com/reset-password?token=abc123'


class _ScalarOneOrNoneResult:
	def __init__(self, value: object | None):
		self._value = value

	def scalar_one_or_none(self) -> object | None:
		return self._value


class _FakeSession:
	def __init__(self, user: object | None) -> None:
		self._user = user

	def execute(self, statement: object) -> _ScalarOneOrNoneResult:
		return _ScalarOneOrNoneResult(self._user)

	def add(self, value: object) -> None:
		raise AssertionError('add() should not be called in this test')

	def flush(self) -> None:
		raise AssertionError('flush() should not be called in this test')


def test_request_password_reset_reports_configured_delivery_channel(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	monkeypatch.setenv('UTW_EMAIL_DELIVERY_BACKEND', 'ses')
	monkeypatch.setenv('UTW_EMAIL_SENDER', 'alerts@example.com')
	monkeypatch.setenv('UTW_AWS_REGION', 'us-east-1')

	result = request_password_reset(
		_FakeSession(None),
		payload=ForgotPasswordRequest(email='missing@example.com'),
	)

	assert result.delivered is False
	assert result.delivery_channel == 'ses'
