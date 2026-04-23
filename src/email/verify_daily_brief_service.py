from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select

from src.api.services.auth_service import register_user
from src.api.services.keyword_profile_service import upsert_keyword_profile
from src.db.models.source import Source
from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.email.daily_brief_service import build_daily_brief_for_user
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR, send_dev_email
from src.ingestion.tender_ingestion_service import ingest_tender
from src.matching.tender_matching_service import match_tender_by_id
from src.shared.schemas.auth import SignupRequest
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest
from src.shared.schemas.tender_ingestion import TenderIngestionInput

SOURCE_NAME = 'Dubai eSupply'
TEST_PASSWORD = 'StrongPass123!'


def run() -> None:
	"""
	Perform an isolated production-grade verification of the daily brief service.

	This script verifies:
	- a unique user can be created
	- a unique tender can be ingested and matched
	- a daily brief can be built for that user
	- the dev email backend can write the brief to disk
	- the rendered brief contains the expected tender information
	"""
	session_factory = get_session_factory()
	unique_marker = f'utw-brief-{uuid4().hex}'
	unique_email = f'{unique_marker}@example.com'
	tender_ref = f'VERIFY-BRIEF-{uuid4().hex[:12].upper()}'
	outbox_dir = DEFAULT_DEV_OUTBOX_DIR / unique_marker

	with session_factory() as session:
		source = session.execute(select(Source).where(Source.name == SOURCE_NAME)).scalar_one_or_none()

		if source is None:
			raise ValueError(f"source '{SOURCE_NAME}' was not found; seed sources first")

		user = register_user(
			session=session,
			payload=SignupRequest(
				email=unique_email,
				password=TEST_PASSWORD,
			),
		)

		profile = upsert_keyword_profile(
			session=session,
			user_id=user.id,
			payload=KeywordProfileUpsertRequest(
				keywords=[unique_marker, 'nonsensical-keyword'],
				alert_enabled=True,
				country_codes=[source.country_code],
				industry_codes=['technology'],
				industry_label='Technology',
			),
		)

		tender, tender_created = ingest_tender(
			session=session,
			payload=TenderIngestionInput(
				source_id=source.id,
				source_url=f'https://esupply.dubai.gov.ae/{unique_marker}',
				title=unique_marker,
				issuing_entity=f'verification-{unique_marker}',
				closing_date=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
				dedupe_key=f'{unique_marker}-dedupe',
				tender_ref=tender_ref,
				opening_date=datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc),
				published_at=datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc),
				category=None,
				ai_summary=unique_marker,
			),
		)

		before_user_match_count = session.execute(
			select(func.count())
			.select_from(TenderMatch)
			.where(
				TenderMatch.user_id == user.id,
				TenderMatch.tender_id == tender.id,
			)
		).scalar_one()

		first_global_created = match_tender_by_id(
			session=session,
			tender_id=tender.id,
		)

		after_first_user_match_count = session.execute(
			select(func.count())
			.select_from(TenderMatch)
			.where(
				TenderMatch.user_id == user.id,
				TenderMatch.tender_id == tender.id,
			)
		).scalar_one()

		first_target_user_created = after_first_user_match_count - before_user_match_count

		second_global_created = match_tender_by_id(
			session=session,
			tender_id=tender.id,
		)

		after_second_user_match_count = session.execute(
			select(func.count())
			.select_from(TenderMatch)
			.where(
				TenderMatch.user_id == user.id,
				TenderMatch.tender_id == tender.id,
			)
		).scalar_one()

		second_target_user_created = after_second_user_match_count - after_first_user_match_count

		session.commit()

		if first_target_user_created != 1:
			raise ValueError(f'expected exactly one new target-user match on first run, got {first_target_user_created}')

		if second_target_user_created != 0:
			raise ValueError(f'expected zero new target-user matches on second run, got {second_target_user_created}')

		brief = build_daily_brief_for_user(
			session=session,
			user_id=user.id,
		)

		if brief is None:
			raise ValueError('expected a daily brief to be built, but got None')

		if len(brief.match_ids) != 1:
			raise ValueError(f'expected exactly one match_id in brief, got {len(brief.match_ids)}')

		if len(brief.tender_ids) != 1:
			raise ValueError(f'expected exactly one tender_id in brief, got {len(brief.tender_ids)}')

		if brief.email_message.to != user.email:
			raise ValueError('daily brief recipient does not match the expected user')

		if tender.title not in brief.email_message.body_text:
			raise ValueError('daily brief body does not contain the expected tender title')

		if unique_marker not in brief.email_message.body_text:
			raise ValueError('daily brief body does not contain the expected unique marker')

		delivery = send_dev_email(
			brief.email_message,
			outbox_dir=outbox_dir,
		)

		if not delivery.output_path.exists():
			raise ValueError('dev email backend did not write the output file')

		rendered_email = delivery.output_path.read_text(encoding='utf-8')
		if tender.title not in rendered_email:
			raise ValueError('rendered email file does not contain the tender title')

		if unique_marker not in rendered_email:
			raise ValueError('rendered email file does not contain the unique marker')

		print(f'verify_brief_email={unique_email}')
		print(f'verify_brief_keyword={unique_marker}')
		print(f'verify_brief_profile_keywords={profile.keywords}')
		print(f'verify_brief_tender_ref={tender_ref}')
		print(f'verify_brief_tender_id={tender.id}')
		print(f'verify_brief_tender_created={tender_created}')
		print(f'verify_brief_first_global_created={first_global_created}')
		print(f'verify_brief_second_global_created={second_global_created}')
		print(f'verify_brief_first_target_user_created={first_target_user_created}')
		print(f'verify_brief_second_target_user_created={second_target_user_created}')
		print(f'verify_brief_match_ids={brief.match_ids}')
		print(f'verify_brief_tender_ids={brief.tender_ids}')
		print(f'verify_brief_subject={brief.email_message.subject}')
		print(f'verify_brief_output_path={delivery.output_path}')
		print(f'verify_brief_message_id={delivery.message_id}')


if __name__ == '__main__':
	run()
