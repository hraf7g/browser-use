from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.shared.schemas.email import EmailMessage

DEFAULT_DEV_OUTBOX_DIR = Path("var/dev_outbox")


@dataclass(frozen=True)
class DevEmailDeliveryResult:
    """Metadata describing a locally written development email."""

    message_id: str
    output_path: Path
    written_at: datetime


def send_dev_email(
    message: EmailMessage,
    *,
    outbox_dir: Path | str = DEFAULT_DEV_OUTBOX_DIR,
) -> DevEmailDeliveryResult:
    """
    Write an email payload to the local development outbox.

    Notes:
        - This backend is for local/dev verification only.
        - It does not send real email.
        - It creates one text file per message for deterministic inspection.
    """
    normalized_outbox_dir = Path(outbox_dir)
    normalized_outbox_dir.mkdir(parents=True, exist_ok=True)

    written_at = datetime.now(timezone.utc)
    message_id = uuid4().hex
    timestamp = written_at.strftime("%Y%m%dT%H%M%SZ")
    safe_recipient = _slugify_for_filename(message.to)
    filename = f"{timestamp}_{safe_recipient}_{message_id}.txt"
    output_path = normalized_outbox_dir / filename

    output_path.write_text(
        _render_email_file(message=message, message_id=message_id, written_at=written_at),
        encoding="utf-8",
    )

    return DevEmailDeliveryResult(
        message_id=message_id,
        output_path=output_path,
        written_at=written_at,
    )


def _render_email_file(
    *,
    message: EmailMessage,
    message_id: str,
    written_at: datetime,
) -> str:
    """Render a deterministic plain-text representation of the email."""
    lines = [
        f"message_id: {message_id}",
        f"written_at: {written_at.isoformat()}",
        f"to: {message.to}",
        f"subject: {message.subject}",
        "",
        message.body_text,
        "",
    ]
    return "\n".join(lines)


def _slugify_for_filename(value: str) -> str:
    """Create a filesystem-safe filename fragment."""
    allowed_chars = []
    for character in value.casefold():
        if character.isalnum():
            allowed_chars.append(character)
        elif character in {".", "_", "-"}:
            allowed_chars.append(character)
        elif character == "@":
            allowed_chars.append("_at_")

    slug = "".join(allowed_chars).strip("._-")
    return slug or "recipient"
