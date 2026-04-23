from __future__ import annotations

import pytest

from src.notifications.notification_preference_service import (
	NotificationPreferenceValidationError,
	_require_boolean_value,
)


def test_require_boolean_value_rejects_explicit_null() -> None:
	with pytest.raises(NotificationPreferenceValidationError, match='email_enabled must not be null'):
		_require_boolean_value(field_name='email_enabled', value=None)


def test_require_boolean_value_accepts_false() -> None:
	assert _require_boolean_value(field_name='email_enabled', value=False) is False
