from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select

from src.api.services.auth_service import register_user
from src.api.services.keyword_profile_service import upsert_keyword_profile
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender
from src.jobs.match_recent_tenders_job_service import run_match_recent_tenders_job
from src.shared.schemas.auth import SignupRequest
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest
from src.shared.schemas.tender_ingestion import TenderIngestionInput

SOURCE_NAME = "Dubai eSupply"
TEST_PASSWORD = "StrongPass123!"


def run() -> None:
    """
    Perform a persisted verification of the recent-tender matching job.

    This script verifies:
        - a deterministic isolated user/profile/tender setup can be matched
        - the matching job persists at least one TenderMatch row
        - rerunning the job does not create duplicate user+tender matches
    """
    session_factory = get_session_factory()
    unique_marker = f"utw-job-match-{uuid4().hex}"
    unique_email = f"{unique_marker}@example.com"
    tender_ref = f"VERIFY-JOB-MATCH-{uuid4().hex[:12].upper()}"
    since = datetime.now(UTC) - timedelta(minutes=5)

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
                keywords=[unique_marker, "توريد", "nonmatching-keyword"],
                alert_enabled=True,
                industry_label="Technology",
            ),
        )

        tender, _ = ingest_tender(
            session=session,
            payload=TenderIngestionInput(
                source_id=source.id,
                source_url=f"https://esupply.dubai.gov.ae/{unique_marker}",
                title=f"{unique_marker} توريد procurement services",
                issuing_entity="Dubai eSupply",
                closing_date=datetime(2026, 5, 15, 12, 0, tzinfo=UTC),
                dedupe_key=f"{unique_marker}-dedupe",
                tender_ref=tender_ref,
                opening_date=datetime(2026, 4, 7, 9, 0, tzinfo=UTC),
                published_at=datetime(2026, 4, 7, 9, 0, tzinfo=UTC),
                category="Technology",
                ai_summary=f"This tender is specifically for {unique_marker}.",
            ),
        )
        session.commit()

    first_created = run_match_recent_tenders_job(since=since)
    second_created = run_match_recent_tenders_job(since=since)

    with session_factory() as session:
        persisted_match_count = session.execute(
            select(func.count())
            .select_from(TenderMatch)
            .where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one()

        target_match = session.execute(
            select(TenderMatch).where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one_or_none()

        persisted_tender = session.execute(
            select(Tender).where(Tender.id == tender.id)
        ).scalar_one()

    if target_match is None:
        raise ValueError("expected target TenderMatch row was not created")

    if first_created < 1:
        raise ValueError(
            f"expected at least one TenderMatch row on first run, got {first_created}"
        )

    if second_created != 0:
        raise ValueError(
            f"expected zero new TenderMatch rows on second run, got {second_created}"
        )

    if persisted_match_count != 1:
        raise ValueError(
            f"expected exactly one persisted user+tender TenderMatch row, got {persisted_match_count}"
        )

    print(f"verify_match_recent_tenders_job_since={since.isoformat()}")
    print(f"verify_match_recent_tenders_job_keyword={unique_marker}")
    print(f"verify_match_recent_tenders_job_user_email={unique_email}")
    print(f"verify_match_recent_tenders_job_tender_id={persisted_tender.id}")
    print(f"verify_match_recent_tenders_job_tender_ref={persisted_tender.tender_ref}")
    print(f"verify_match_recent_tenders_job_first_created={first_created}")
    print(f"verify_match_recent_tenders_job_second_created={second_created}")
    print(f"verify_match_recent_tenders_job_persisted_match_count={persisted_match_count}")
    print(
        "verify_match_recent_tenders_job_matched_keywords="
        f"{target_match.matched_keywords}"
    )


if __name__ == "__main__":
    run()
