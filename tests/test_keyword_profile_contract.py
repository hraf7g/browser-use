from __future__ import annotations

import uuid

import pytest

from src.api.services.keyword_profile_service import build_keyword_profile_response
from src.db.models.keyword_profile import KeywordProfile
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest


def test_keyword_profile_request_normalizes_supported_country_codes() -> None:
	payload = KeywordProfileUpsertRequest(
		keywords=['construction'],
		alert_enabled=True,
		country_codes=['sa', ' QA ', 'sa'],
		industry_codes=['technology', ' construction ', 'technology'],
		industry_label='Infrastructure',
	)

	assert payload.country_codes == ['SA', 'QA']
	assert payload.industry_codes == ['technology', 'construction']


def test_keyword_profile_request_rejects_unsupported_country_codes() -> None:
	with pytest.raises(ValueError, match="country code 'US' is not supported"):
		KeywordProfileUpsertRequest(
			keywords=['construction'],
			alert_enabled=True,
			country_codes=['US'],
		)


def test_build_keyword_profile_response_includes_country_codes() -> None:
	profile = KeywordProfile(
		id=uuid.uuid4(),
		user_id=uuid.uuid4(),
		keywords=['construction'],
		alert_enabled=True,
		country_codes=['SA', 'QA'],
		industry_codes=['technology', 'construction'],
		industry_label='Infrastructure',
	)

	response = build_keyword_profile_response(profile)

	assert response.country_codes == ['SA', 'QA']
	assert response.industry_codes == ['technology', 'construction']


def test_keyword_profile_request_rejects_unsupported_industry_codes() -> None:
	with pytest.raises(ValueError, match="industry code 'retail' is not supported"):
		KeywordProfileUpsertRequest(
			keywords=['construction'],
			alert_enabled=True,
			industry_codes=['retail'],
		)
