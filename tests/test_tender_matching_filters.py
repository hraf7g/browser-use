from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import cast

from sqlalchemy.orm import Session

from src.db.models.keyword_profile import KeywordProfile
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.matching.tender_matching_service import (
	_country_scope_allows_profile,
	_industry_scope_allows_profile,
	_profile_allows_tender_scope,
	match_tender,
)


def _build_profile(*, country_codes: list[str], industry_codes: list[str]) -> KeywordProfile:
	return KeywordProfile(
		id=uuid.uuid4(),
		user_id=uuid.uuid4(),
		keywords=['network'],
		alert_enabled=True,
		country_codes=country_codes,
		industry_codes=industry_codes,
		industry_label='Technology',
	)


def _build_source(*, country_code: str) -> Source:
	return Source(
		id=uuid.uuid4(),
		name=f'Source {country_code}',
		base_url=f'https://{country_code.lower()}.example.com',
		country_code=country_code,
		country_name=country_code,
		lifecycle='live',
		status='healthy',
		failure_count=0,
		last_successful_run_at=None,
		last_failed_run_at=None,
		notes=None,
	)


def _build_tender(*, source_id: uuid.UUID, industry_codes: list[str]) -> Tender:
	return Tender(
		id=uuid.uuid4(),
		source_id=source_id,
		tender_ref='REF-1',
		source_url='https://example.com/tender',
		title='Technology network support services',
		issuing_entity='Digital Authority',
		closing_date=None,
		opening_date=None,
		published_at=None,
		category='Technology',
		industry_codes=industry_codes,
		primary_industry_code=None if not industry_codes else industry_codes[0],
		ai_summary='Network support',
		dedupe_key='dedupe-1',
		search_text='technology network support',
	)


def test_country_scope_allows_unscoped_profiles() -> None:
	profile = _build_profile(country_codes=[], industry_codes=[])
	source = _build_source(country_code='AE')

	assert _country_scope_allows_profile(profile=profile, source=source) is True


def test_country_scope_blocks_non_matching_source_country() -> None:
	profile = _build_profile(country_codes=['SA'], industry_codes=[])
	source = _build_source(country_code='AE')

	assert _country_scope_allows_profile(profile=profile, source=source) is False


def test_industry_scope_requires_intersection_when_profile_is_scoped() -> None:
	profile = _build_profile(country_codes=[], industry_codes=['technology'])
	tender = _build_tender(source_id=uuid.uuid4(), industry_codes=['healthcare'])

	assert _industry_scope_allows_profile(profile=profile, tender=tender) is False


def test_profile_scope_requires_both_country_and_industry_filters_to_pass() -> None:
	source = _build_source(country_code='AE')
	tender = _build_tender(source_id=source.id, industry_codes=['technology'])

	profile = _build_profile(country_codes=['AE'], industry_codes=['technology'])
	assert _profile_allows_tender_scope(profile=profile, tender=tender, source=source) is True

	blocked_by_country = _build_profile(country_codes=['SA'], industry_codes=['technology'])
	assert _profile_allows_tender_scope(profile=blocked_by_country, tender=tender, source=source) is False

	blocked_by_industry = _build_profile(country_codes=['AE'], industry_codes=['construction'])
	assert _profile_allows_tender_scope(profile=blocked_by_industry, tender=tender, source=source) is False


class _FakeScalarRows:
	def __init__(self, values: Sequence[object]) -> None:
		self._values = values

	def all(self) -> list[object]:
		return list(self._values)


class _FakeExecuteResult:
	def __init__(self, values: Sequence[object]) -> None:
		self._values = values

	def scalars(self) -> _FakeScalarRows:
		return _FakeScalarRows(self._values)


class _FakeMatchingSession:
	def __init__(self, *, source: Source, profiles: list[KeywordProfile], existing_user_ids: list[uuid.UUID]) -> None:
		self._source = source
		self._profiles = profiles
		self._existing_user_ids = existing_user_ids
		self._execute_calls = 0
		self.added: list[TenderMatch] = []
		self.flush_called = False

	def get(self, model, identifier):
		if model is Source and identifier == self._source.id:
			return self._source
		return None

	def execute(self, _query):
		self._execute_calls += 1
		if self._execute_calls == 1:
			return _FakeExecuteResult(self._profiles)
		if self._execute_calls == 2:
			return _FakeExecuteResult(self._existing_user_ids)
		raise AssertionError(f'unexpected execute call {self._execute_calls}')

	def add(self, item: TenderMatch) -> None:
		self.added.append(item)

	def flush(self) -> None:
		self.flush_called = True


def test_match_tender_creates_one_match_when_scope_and_keywords_both_pass() -> None:
	source = _build_source(country_code='AE')
	tender = _build_tender(source_id=source.id, industry_codes=['technology'])
	profile = _build_profile(country_codes=['AE'], industry_codes=['technology'])
	session = _FakeMatchingSession(source=source, profiles=[profile], existing_user_ids=[])

	created_count = match_tender(session=cast(Session, session), tender=tender)

	assert created_count == 1
	assert session.flush_called is True
	assert len(session.added) == 1
	assert session.added[0].user_id == profile.user_id
	assert session.added[0].tender_id == tender.id
	assert session.added[0].matched_keywords == ['network']
	assert session.added[0].matched_country_codes == ['AE']
	assert session.added[0].matched_industry_codes == ['technology']


def test_match_tender_blocks_keyword_match_when_country_scope_fails() -> None:
	source = _build_source(country_code='AE')
	tender = _build_tender(source_id=source.id, industry_codes=['technology'])
	profile = _build_profile(country_codes=['SA'], industry_codes=['technology'])
	session = _FakeMatchingSession(source=source, profiles=[profile], existing_user_ids=[])

	created_count = match_tender(session=cast(Session, session), tender=tender)

	assert created_count == 0
	assert session.flush_called is False
	assert session.added == []


def test_match_tender_records_no_scope_evidence_for_unscoped_profiles() -> None:
	source = _build_source(country_code='AE')
	tender = _build_tender(source_id=source.id, industry_codes=['technology'])
	profile = _build_profile(country_codes=[], industry_codes=[])
	session = _FakeMatchingSession(source=source, profiles=[profile], existing_user_ids=[])

	created_count = match_tender(session=cast(Session, session), tender=tender)

	assert created_count == 1
	assert len(session.added) == 1
	assert session.added[0].matched_country_codes == []
	assert session.added[0].matched_industry_codes == []
