from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.api.services.activity_overview_service import _build_match_summary as build_activity_match_summary
from src.api.services.tender_details_service import _build_match_summary as build_tender_details_match_summary
from src.api.services.tender_service import build_tender_list_item
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.email.daily_brief_service import _render_tender_match_block as render_daily_brief_match_block
from src.notifications.instant_alert_service import _render_tender_match_block as render_instant_alert_match_block


def _build_tender() -> Tender:
	return Tender(
		id=uuid.uuid4(),
		source_id=uuid.uuid4(),
		tender_ref='REF-42',
		source_url='https://example.com/tenders/42',
		title='Technology network support services',
		issuing_entity='Digital Authority',
		closing_date=None,
		opening_date=None,
		published_at=None,
		category='Technology',
		industry_codes=['technology'],
		primary_industry_code='technology',
		ai_summary='Network support procurement.',
		dedupe_key='dedupe-42',
		search_text='technology network support procurement',
		created_at=datetime(2026, 4, 18, tzinfo=timezone.utc),
	)


def _build_source() -> Source:
	return Source(
		id=uuid.uuid4(),
		name='Dubai eSupply',
		base_url='https://esupply.dubai.gov.ae',
		country_code='AE',
		country_name='United Arab Emirates',
		lifecycle='live',
		status='healthy',
		failure_count=0,
		last_successful_run_at=None,
		last_failed_run_at=None,
		notes=None,
	)


def _build_match(*, tender_id: uuid.UUID) -> TenderMatch:
	return TenderMatch(
		id=uuid.uuid4(),
		user_id=uuid.uuid4(),
		tender_id=tender_id,
		matched_keywords=['network'],
		matched_country_codes=['AE'],
		matched_industry_codes=['technology'],
	)


def test_build_tender_list_item_includes_persisted_match_scope_evidence() -> None:
	tender = _build_tender()

	item = build_tender_list_item(
		tender,
		source_name='Dubai eSupply',
		is_matched=True,
		matched_keywords=['network'],
		matched_country_codes=['AE'],
		matched_industry_codes=['technology'],
	)

	assert item.matched_keywords == ['network']
	assert item.matched_country_codes == ['AE']
	assert item.matched_industry_codes == ['technology']


def test_activity_match_summary_mentions_country_industry_and_keywords() -> None:
	summary = build_activity_match_summary(
		tender_title='Technology network support services',
		keywords=['network'],
		matched_country_codes=['AE'],
		matched_industry_codes=['technology'],
	)

	assert summary == 'Technology network support services matched on countries AE, industries technology, keywords network.'


def test_tender_details_match_summary_mentions_country_industry_and_keywords() -> None:
	summary = build_tender_details_match_summary(
		matched_keywords=['network'],
		matched_country_codes=['AE'],
		matched_industry_codes=['technology'],
	)

	assert summary == 'Matched countries: AE. Matched industries: technology. Matched keywords: network.'


def test_email_renderers_include_scope_reason_lines() -> None:
	tender = _build_tender()
	source = _build_source()
	match = _build_match(tender_id=tender.id)

	daily_brief_block = render_daily_brief_match_block(
		position=1,
		tender=tender,
		source=source,
		tender_match=match,
	)
	instant_alert_block = render_instant_alert_match_block(
		position=1,
		tender=tender,
		source=source,
		tender_match=match,
	)

	assert 'Matched Countries: United Arab Emirates' in daily_brief_block
	assert 'Matched Industries: Technology' in daily_brief_block
	assert 'Matched Countries: United Arab Emirates' in instant_alert_block
	assert 'Matched Industries: Technology' in instant_alert_block
