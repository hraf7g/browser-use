from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR, send_dev_email
from src.shared.config.settings import Settings, get_settings
from src.shared.schemas.email import EmailMessage

EmailDeliveryBackendName = Literal['dev_outbox', 'ses']


class EmailDeliveryBackendError(RuntimeError):
	"""Raised when the configured email backend cannot deliver a message."""


@dataclass(frozen=True)
class EmailDeliveryBackendResult:
	"""Normalized email-delivery metadata across local and production backends."""

	message_id: str
	delivered_at: datetime
	provider: EmailDeliveryBackendName
	output_path: Path | None = None


def get_email_delivery_backend_name(settings: Settings | None = None) -> EmailDeliveryBackendName:
	"""Return the configured backend name."""
	cfg = settings or get_settings()
	return cfg.email_delivery_backend


def send_email_message(
	message: EmailMessage,
	*,
	outbox_dir: Path | str = DEFAULT_DEV_OUTBOX_DIR,
	settings: Settings | None = None,
) -> EmailDeliveryBackendResult:
	"""Deliver an email using the configured backend."""
	cfg = settings or get_settings()
	backend_name = cfg.email_delivery_backend

	if backend_name == 'dev_outbox':
		delivery_result = send_dev_email(message, outbox_dir=outbox_dir)
		return EmailDeliveryBackendResult(
			message_id=delivery_result.message_id,
			delivered_at=delivery_result.written_at,
			provider='dev_outbox',
			output_path=delivery_result.output_path,
		)

	if backend_name == 'ses':
		return _send_ses_email_message(message=message, settings=cfg)

	raise EmailDeliveryBackendError(f'unsupported email backend: {backend_name!r}')


def _send_ses_email_message(
	*,
	message: EmailMessage,
	settings: Settings,
) -> EmailDeliveryBackendResult:
	"""Deliver one plain-text email using Amazon SES v2."""
	try:
		import boto3
	except ImportError as exc:  # pragma: no cover - exercised via unit tests with monkeypatching
		raise EmailDeliveryBackendError(
			"SES delivery requires boto3 to be installed; run `uv sync --extra aws`."
		) from exc

	client = boto3.client('sesv2', region_name=settings.aws_region)
	request: dict[str, object] = {
		'FromEmailAddress': settings.email_sender,
		'Destination': {'ToAddresses': [message.to]},
		'Content': {
			'Simple': {
				'Subject': {'Data': message.subject, 'Charset': 'UTF-8'},
				'Body': {
					'Text': {'Data': message.body_text, 'Charset': 'UTF-8'},
				},
			},
		},
	}

	if settings.email_reply_to:
		request['ReplyToAddresses'] = [settings.email_reply_to]
	if settings.email_ses_configuration_set:
		request['ConfigurationSetName'] = settings.email_ses_configuration_set
	if settings.email_ses_from_arn:
		request['FromEmailAddressIdentityArn'] = settings.email_ses_from_arn

	response = client.send_email(**request)
	message_id = str((response or {}).get('MessageId', '')).strip()
	if not message_id:
		raise EmailDeliveryBackendError('SES response did not include a MessageId')

	return EmailDeliveryBackendResult(
		message_id=message_id,
		delivered_at=datetime.now(timezone.utc),
		provider='ses',
		output_path=None,
	)
