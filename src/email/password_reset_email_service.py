from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from src.email.backend import send_email_message
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR
from src.shared.schemas.email import EmailMessage


@dataclass(frozen=True)
class PasswordResetEmailDispatchResult:
	"""Metadata describing a delivered password reset link."""

	reset_url: str
	output_path: Path | None
	message_id: str
	provider: str


def dispatch_password_reset_email(
	*,
	recipient_email: str,
	reset_token: str,
	frontend_base_url: str,
	outbox_dir: Path | str = DEFAULT_DEV_OUTBOX_DIR,
) -> PasswordResetEmailDispatchResult:
	"""Deliver one password-reset email using the configured backend."""
	reset_url = _build_reset_url(
		frontend_base_url=frontend_base_url,
		reset_token=reset_token,
	)
	message = EmailMessage(
		to=recipient_email,
		subject='Tender Watch password reset',
		body_text=(
			'We received a request to reset your Tender Watch password.\n\n'
			f'Use this link to choose a new password:\n{reset_url}\n\n'
			'This link expires automatically. If you did not request a password reset, you can ignore this email.'
		),
	)
	delivery_result = send_email_message(
		message,
		outbox_dir=outbox_dir,
	)
	return PasswordResetEmailDispatchResult(
		reset_url=reset_url,
		output_path=delivery_result.output_path,
		message_id=delivery_result.message_id,
		provider=delivery_result.provider,
	)


def _build_reset_url(*, frontend_base_url: str, reset_token: str) -> str:
	normalized_base_url = frontend_base_url.rstrip('/')
	return f'{normalized_base_url}/reset-password?token={quote(reset_token)}'
