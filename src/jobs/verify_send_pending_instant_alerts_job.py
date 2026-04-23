from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from src.api.services.auth_service import register_user
from src.api.services.keyword_profile_service import upsert_keyword_profile
from src.db.models.email_delivery import EmailDelivery
from src.db.models.source import Source
from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender
from src.jobs.match_recent_tenders_job_service import run_match_recent_tenders_job
from src.jobs.send_pending_instant_alerts_job_service import (
	run_send_pending_instant_alerts_job,
)
from src.jobs.verify_match_recent_tenders_job import TEST_PASSWORD
from src.notifications.notification_preference_service import (
	update_notification_preference,
)
from src.shared.schemas.auth import SignupRequest
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest
from src.shared.schemas.notification_preference import (
	NotificationPreferenceUpdateRequest,
)
from src.shared.schemas.tender_ingestion import TenderIngestionInput

SOURCE_NAME = 'Dubai eSupply'


def run() -> None:
	"""
	Perform a persisted verification that instant-alert dispatch respects preferences.

	This script verifies:
	    - an eligible user with enabled email/instant-alert preferences receives a delivery
	    - a blocked user with disabled instant alerts/email does not receive a delivery
	    - TenderMatch.alerted_at is updated for the eligible user only
	    - TenderMatch.sent_at remains untouched so daily briefs can still operate later
	"""
	session_factory = get_session_factory()
	unique_marker = f'utw-instant-alert-{uuid4().hex}'
	since = datetime.now(UTC)

	with session_factory() as session:
		source = session.execute(select(Source).where(Source.name == SOURCE_NAME)).scalar_one_or_none()
		if source is None:
			raise ValueError(f"source '{SOURCE_NAME}' was not found; seed sources first")

		eligible_user = register_user(
			session=session,
			payload=SignupRequest(
				email=f'{unique_marker}-eligible@example.com',
				password=TEST_PASSWORD,
			),
		)
		blocked_user = register_user(
			session=session,
			payload=SignupRequest(
				email=f'{unique_marker}-blocked@example.com',
				password=TEST_PASSWORD,
			),
		)
		eligible_user_id = eligible_user.id
		eligible_user_email = eligible_user.email
		blocked_user_id = blocked_user.id
		blocked_user_email = blocked_user.email

		upsert_keyword_profile(
			session=session,
			user_id=eligible_user_id,
			payload=KeywordProfileUpsertRequest(
				keywords=[f'{unique_marker}-eligible', 'توريد'],
				alert_enabled=True,
				country_codes=[source.country_code],
				industry_codes=['technology'],
				industry_label='Technology',
			),
		)
		upsert_keyword_profile(
			session=session,
			user_id=blocked_user_id,
			payload=KeywordProfileUpsertRequest(
				keywords=[f'{unique_marker}-blocked', 'توريد'],
				alert_enabled=True,
				country_codes=[source.country_code],
				industry_codes=['technology'],
				industry_label='Technology',
			),
		)

		update_notification_preference(
			session,
			user_id=eligible_user_id,
			payload=NotificationPreferenceUpdateRequest(
				email_enabled=True,
				instant_alert_enabled=True,
				daily_brief_enabled=True,
				preferred_language='auto',
			),
		)
		update_notification_preference(
			session,
			user_id=blocked_user_id,
			payload=NotificationPreferenceUpdateRequest(
				email_enabled=False,
				instant_alert_enabled=False,
				daily_brief_enabled=True,
				preferred_language='en',
			),
		)

		eligible_tender, _ = ingest_tender(
			session=session,
			payload=TenderIngestionInput(
				source_id=source.id,
				source_url=f'https://esupply.dubai.gov.ae/{unique_marker}-eligible',
				title=f'{unique_marker}-eligible توريد instant alert tender',
				issuing_entity='Dubai eSupply',
				closing_date=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
				dedupe_key=f'{unique_marker}-eligible-dedupe',
				tender_ref=f'INSTANT-ELIGIBLE-{uuid4().hex[:8].upper()}',
				opening_date=datetime(2026, 4, 8, 9, 0, tzinfo=UTC),
				published_at=datetime(2026, 4, 8, 9, 0, tzinfo=UTC),
				category='Technology',
				ai_summary=f'This tender is specifically for {unique_marker}-eligible.',
			),
		)
		eligible_tender_id = eligible_tender.id

		blocked_tender, _ = ingest_tender(
			session=session,
			payload=TenderIngestionInput(
				source_id=source.id,
				source_url=f'https://esupply.dubai.gov.ae/{unique_marker}-blocked',
				title=f'{unique_marker}-blocked توريد instant alert tender',
				issuing_entity='Dubai eSupply',
				closing_date=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
				dedupe_key=f'{unique_marker}-blocked-dedupe',
				tender_ref=f'INSTANT-BLOCKED-{uuid4().hex[:8].upper()}',
				opening_date=datetime(2026, 4, 8, 9, 0, tzinfo=UTC),
				published_at=datetime(2026, 4, 8, 9, 0, tzinfo=UTC),
				category='Technology',
				ai_summary=f'This tender is specifically for {unique_marker}-blocked.',
			),
		)
		blocked_tender_id = blocked_tender.id
		session.commit()

	matches_created = run_match_recent_tenders_job(since=since)
	if matches_created < 2:
		raise ValueError(f'expected at least two TenderMatch rows before instant-alert job, got {matches_created}')

	result = run_send_pending_instant_alerts_job()

	with session_factory() as session:
		eligible_deliveries = (
			session.execute(
				select(EmailDelivery)
				.where(
					EmailDelivery.user_id == eligible_user_id,
					EmailDelivery.delivery_type == 'instant_alert',
				)
				.order_by(EmailDelivery.attempted_at.asc(), EmailDelivery.id.asc())
			)
			.scalars()
			.all()
		)
		blocked_deliveries = (
			session.execute(
				select(EmailDelivery)
				.where(
					EmailDelivery.user_id == blocked_user_id,
					EmailDelivery.delivery_type == 'instant_alert',
				)
				.order_by(EmailDelivery.attempted_at.asc(), EmailDelivery.id.asc())
			)
			.scalars()
			.all()
		)

		eligible_match = session.execute(
			select(TenderMatch).where(
				TenderMatch.user_id == eligible_user_id,
				TenderMatch.tender_id == eligible_tender_id,
			)
		).scalar_one_or_none()
		blocked_match = session.execute(
			select(TenderMatch).where(
				TenderMatch.user_id == blocked_user_id,
				TenderMatch.tender_id == blocked_tender_id,
			)
		).scalar_one_or_none()

	if not eligible_deliveries:
		raise ValueError('expected eligible user to receive an instant-alert delivery')

	if blocked_deliveries:
		raise ValueError('expected blocked user to receive zero instant-alert deliveries')

	if eligible_match is None:
		raise ValueError("expected eligible user's TenderMatch row to exist")

	if eligible_match.alerted_at is None:
		raise ValueError("expected eligible user's TenderMatch.alerted_at to be populated")

	if eligible_match.sent_at is not None:
		raise ValueError("expected eligible user's TenderMatch.sent_at to remain None")

	if blocked_match is None:
		raise ValueError("expected blocked user's TenderMatch row to exist")

	if blocked_match.alerted_at is not None:
		raise ValueError("expected blocked user's TenderMatch.alerted_at to remain None")

	if blocked_match.sent_at is not None:
		raise ValueError("expected blocked user's TenderMatch.sent_at to remain None")

	print(f'verify_instant_alert_job_overall_status={result.overall_status}')
	print(f'verify_instant_alert_job_processed_user_count={result.processed_user_count}')
	print(f'verify_instant_alert_job_sent_delivery_count={result.sent_delivery_count}')
	print(f'verify_instant_alert_job_skipped_user_count={result.skipped_user_count}')
	print(f'verify_instant_alert_job_eligible_email={eligible_user_email}')
	print(f'verify_instant_alert_job_blocked_email={blocked_user_email}')
	print(f'verify_instant_alert_job_eligible_delivery_count={len(eligible_deliveries)}')
	print(f'verify_instant_alert_job_blocked_delivery_count={len(blocked_deliveries)}')
	print(f'verify_instant_alert_job_eligible_match_alerted_at={eligible_match.alerted_at.isoformat()}')
	print(f'verify_instant_alert_job_eligible_match_sent_at={eligible_match.sent_at}')
	print(f'verify_instant_alert_job_blocked_match_alerted_at={blocked_match.alerted_at}')


if __name__ == '__main__':
	run()
