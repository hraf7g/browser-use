from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select

from src.api.services.auth_service import register_user
from src.api.services.keyword_profile_service import upsert_keyword_profile
from src.db.models.email_delivery import EmailDelivery
from src.db.models.source import Source
from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender
from src.jobs.verify_match_recent_tenders_job import TEST_PASSWORD
from src.jobs.match_recent_tenders_job_service import run_match_recent_tenders_job
from src.jobs.send_pending_daily_briefs_job_service import (
    run_send_pending_daily_briefs_job,
)
from src.shared.schemas.auth import SignupRequest
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest
from src.shared.schemas.tender_ingestion import TenderIngestionInput

SOURCE_NAME = "Dubai eSupply"


def run() -> None:
    """
    Perform a persisted verification of the pending daily-brief dispatch job.

    This script verifies:
        - an isolated matched tender can be made eligible for briefing
        - the job persists at least one EmailDelivery row
        - the delivery row has the expected status
        - included TenderMatch rows are marked sent
    """
    session_factory = get_session_factory()
    unique_marker = f"utw-daily-brief-job-{uuid4().hex}"
    unique_email = f"{unique_marker}@example.com"
    tender_ref = f"VERIFY-DAILY-BRIEF-{uuid4().hex[:12].upper()}"
    since = datetime.now(UTC)

    with session_factory() as session:
        source = session.execute(
            select(Source).where(Source.name == SOURCE_NAME)
        ).scalar_one_or_none()
        if source is None:
            raise ValueError(
                f"source '{SOURCE_NAME}' was not found; seed sources first"
            )

        user = register_user(
            session=session,
            payload=SignupRequest(
                email=unique_email,
                password=TEST_PASSWORD,
            ),
        )

        upsert_keyword_profile(
            session=session,
            user_id=user.id,
            payload=KeywordProfileUpsertRequest(
                keywords=[unique_marker, "توريد"],
                alert_enabled=True,
                industry_label="Technology",
            ),
        )

        tender, _ = ingest_tender(
            session=session,
            payload=TenderIngestionInput(
                source_id=source.id,
                source_url=f"https://esupply.dubai.gov.ae/{unique_marker}",
                title=f"{unique_marker} توريد daily brief tender",
                issuing_entity="Dubai eSupply",
                closing_date=datetime(2026, 5, 30, 12, 0, tzinfo=UTC),
                dedupe_key=f"{unique_marker}-dedupe",
                tender_ref=tender_ref,
                opening_date=datetime(2026, 4, 8, 9, 0, tzinfo=UTC),
                published_at=datetime(2026, 4, 8, 9, 0, tzinfo=UTC),
                category="Technology",
                ai_summary=f"This tender is specifically for {unique_marker}.",
            ),
        )
        session.commit()

    matches_created = run_match_recent_tenders_job(since=since)
    if matches_created < 1:
        raise ValueError(
            f"expected at least one TenderMatch row before daily brief job, got {matches_created}"
        )

    result = run_send_pending_daily_briefs_job()

    with session_factory() as session:
        email_deliveries = session.execute(
            select(EmailDelivery)
            .where(
                EmailDelivery.user_id == user.id,
                EmailDelivery.delivery_type == "daily_brief",
            )
            .order_by(EmailDelivery.attempted_at.asc(), EmailDelivery.id.asc())
        ).scalars().all()

        if not email_deliveries:
            raise ValueError("expected at least one EmailDelivery row, got zero")

        latest_delivery = email_deliveries[-1]
        if latest_delivery.status != "sent":
            raise ValueError(
                f"expected latest daily brief delivery status 'sent', got {latest_delivery.status}"
            )

        if latest_delivery.sent_at is None:
            raise ValueError("expected latest daily brief delivery sent_at to be populated")

        target_match = session.execute(
            select(TenderMatch).where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one_or_none()

        if target_match is None:
            raise ValueError("expected target TenderMatch row to exist")

        if target_match.sent_at is None:
            raise ValueError("expected target TenderMatch.sent_at to be populated")

    print(f"verify_daily_brief_job_overall_status={result.overall_status}")
    print(
        f"verify_daily_brief_job_processed_user_count={result.processed_user_count}"
    )
    print(f"verify_daily_brief_job_sent_delivery_count={result.sent_delivery_count}")
    print(f"verify_daily_brief_job_skipped_user_count={result.skipped_user_count}")
    print(f"verify_daily_brief_job_user_email={unique_email}")
    print(f"verify_daily_brief_job_tender_ref={tender_ref}")
    print(f"verify_daily_brief_job_email_delivery_count={len(email_deliveries)}")
    print(f"verify_daily_brief_job_latest_delivery_id={latest_delivery.id}")
    print(f"verify_daily_brief_job_latest_delivery_status={latest_delivery.status}")
    print(
        "verify_daily_brief_job_target_match_sent_at="
        f"{target_match.sent_at.isoformat()}"
    )


if __name__ == "__main__":
    run()
