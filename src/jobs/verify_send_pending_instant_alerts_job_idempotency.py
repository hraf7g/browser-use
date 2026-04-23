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
	Perform a persisted idempotency verification of the instant-alert job.

	This script verifies:
	    - the first run creates one target user's instant-alert delivery
	    - the second run does not create a duplicate delivery for that target user
	    - the target TenderMatch remains marked alerted after the first run
	"""
	session_factory = get_session_factory()
	unique_marker = f'utw-instant-alert-idempotency-{uuid4().hex}'
	since = datetime.now(UTC)

	with session_factory() as session:
		source = session.execute(select(Source).where(Source.name == SOURCE_NAME)).scalar_one_or_none()
		if source is None:
			raise ValueError(f"source '{SOURCE_NAME}' was not found; seed sources first")

		user = register_user(
			session=session,
			payload=SignupRequest(
				email=f'{unique_marker}@example.com',
				password=TEST_PASSWORD,
			),
		)
		user_id = user.id
		user_email = user.email

		upsert_keyword_profile(
			session=session,
			user_id=user_id,
			payload=KeywordProfileUpsertRequest(
				keywords=[unique_marker, 'توريد'],
				alert_enabled=True,
				country_codes=[source.country_code],
				industry_codes=['technology'],
				industry_label='Technology',
			),
		)

		update_notification_preference(
			session,
			user_id=user_id,
			payload=NotificationPreferenceUpdateRequest(
				email_enabled=True,
				instant_alert_enabled=True,
				daily_brief_enabled=True,
				preferred_language='auto',
			),
		)

		tender, _ = ingest_tender(
			session=session,
			payload=TenderIngestionInput(
				source_id=source.id,
				source_url=f'https://esupply.dubai.gov.ae/{unique_marker}',
				title=f'{unique_marker} توريد instant alert idempotency tender',
				issuing_entity='Dubai eSupply',
				closing_date=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
				dedupe_key=f'{unique_marker}-dedupe',
				tender_ref=f'INSTANT-IDEMP-{uuid4().hex[:8].upper()}',
				opening_date=datetime(2026, 4, 8, 9, 0, tzinfo=UTC),
				published_at=datetime(2026, 4, 8, 9, 0, tzinfo=UTC),
				category='Technology',
				ai_summary=f'This tender is specifically for {unique_marker}.',
			),
		)
		tender_id = tender.id
		session.commit()

	matches_created = run_match_recent_tenders_job(since=since)
	if matches_created < 1:
		raise ValueError(f'expected at least one TenderMatch row before instant-alert idempotency test, got {matches_created}')

	first_result = run_send_pending_instant_alerts_job()
	second_result = run_send_pending_instant_alerts_job()

	with session_factory() as session:
		user_deliveries = (
			session.execute(
				select(EmailDelivery)
				.where(
					EmailDelivery.user_id == user_id,
					EmailDelivery.delivery_type == 'instant_alert',
				)
				.order_by(EmailDelivery.attempted_at.asc(), EmailDelivery.id.asc())
			)
			.scalars()
			.all()
		)

		target_match = session.execute(
			select(TenderMatch).where(
				TenderMatch.user_id == user_id,
				TenderMatch.tender_id == tender_id,
			)
		).scalar_one_or_none()

	if len(user_deliveries) != 1:
		raise ValueError(f'expected exactly one instant-alert delivery for target user, got {len(user_deliveries)}')

	if target_match is None:
		raise ValueError('expected target TenderMatch row to exist')

	if target_match.alerted_at is None:
		raise ValueError('expected target TenderMatch.alerted_at to be populated')

	if target_match.sent_at is not None:
		raise ValueError('expected target TenderMatch.sent_at to remain None')

	print(f'verify_instant_alert_job_idempotency_first_status={first_result.overall_status}')
	print(f'verify_instant_alert_job_idempotency_first_sent={first_result.sent_delivery_count}')
	print(f'verify_instant_alert_job_idempotency_second_status={second_result.overall_status}')
	print(f'verify_instant_alert_job_idempotency_second_sent={second_result.sent_delivery_count}')
	print(f'verify_instant_alert_job_idempotency_user_email={user_email}')
	print(f'verify_instant_alert_job_idempotency_user_delivery_count={len(user_deliveries)}')
	print(f'verify_instant_alert_job_idempotency_target_match_alerted_at={target_match.alerted_at.isoformat()}')
	print(f'verify_instant_alert_job_idempotency_target_match_sent_at={target_match.sent_at}')


if __name__ == '__main__':
	run()
