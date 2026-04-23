from __future__ import annotations

import json
import logging

from src.shared.logging.logger import JsonFormatter


def test_json_formatter_includes_extra_fields() -> None:
	record = logging.makeLogRecord(
		{
			'name': 'test.logger',
			'levelno': logging.INFO,
			'levelname': 'INFO',
			'msg': 'operator_action',
			'action': 'run_source',
			'access_path': 'operator_session',
			'operator_user_id': 'operator-1',
		}
	)

	payload = json.loads(JsonFormatter().format(record))

	assert payload['message'] == 'operator_action'
	assert payload['action'] == 'run_source'
	assert payload['access_path'] == 'operator_session'
	assert payload['operator_user_id'] == 'operator-1'
