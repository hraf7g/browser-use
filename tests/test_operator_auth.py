from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from src.api.dependencies.operator_auth import require_operator_access


def test_require_operator_access_returns_operator_session_context() -> None:
	context = require_operator_access(
		current_user=SimpleNamespace(
			id=UUID('00000000-0000-0000-0000-000000000911'),
			email='operator@example.com',
			is_operator=True,
		),
		x_operator_key=None,
	)

	assert context.access_path == 'operator_session'
	assert context.operator_user_id == '00000000-0000-0000-0000-000000000911'
	assert context.operator_email == 'operator@example.com'


def test_require_operator_access_rejects_non_operator_session() -> None:
	with pytest.raises(HTTPException) as exc_info:
		require_operator_access(
			current_user=SimpleNamespace(
				id=UUID('00000000-0000-0000-0000-000000000912'),
				email='user@example.com',
				is_operator=False,
			),
			x_operator_key=None,
		)

	assert exc_info.value.status_code == 403
	assert exc_info.value.detail == 'operator role required'
