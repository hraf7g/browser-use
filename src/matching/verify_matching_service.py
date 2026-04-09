from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select

from src.api.services.auth_service import register_user
from src.api.services.keyword_profile_service import upsert_keyword_profile
from src.db.models.source import Source
from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender
from src.matching.tender_matching_service import match_tender_by_id
from src.shared.schemas.auth import SignupRequest
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest
from src.shared.schemas.tender_ingestion import TenderIngestionInput

SOURCE_NAME = "Dubai eSupply"
TEST_PASSWORD = "StrongPass123!"


def run() -> None:
    """
    Perform an isolated production-grade verification of the tender matching service.

    This script verifies:
    - a newly ingested tender can be matched
    - a freshly created user with a unique keyword receives exactly one target match
    - rerunning matching is idempotent for that same user+tender pair
    """
    session_factory = get_session_factory()
    unique_marker = f"utw-match-{uuid4().hex}"
    unique_email = f"{unique_marker}@example.com"
    tender_ref = f"VERIFY-MATCH-{uuid4().hex[:12].upper()}"

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

        profile = upsert_keyword_profile(
            session=session,
            user_id=user.id,
            payload=KeywordProfileUpsertRequest(
                keywords=[unique_marker, "nonmatching-keyword"],
                alert_enabled=True,
                industry_label="Technology",
            ),
        )

        tender, tender_created = ingest_tender(
            session=session,
            payload=TenderIngestionInput(
                source_id=source.id,
                source_url=f"https://esupply.dubai.gov.ae/{unique_marker}",
                title=f"{unique_marker} procurement services",
                issuing_entity="Dubai eSupply",
                closing_date=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
                dedupe_key=f"{unique_marker}-dedupe",
                tender_ref=tender_ref,
                opening_date=datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc),
                published_at=datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc),
                category="Technology",
                ai_summary=f"This tender is specifically for {unique_marker}.",
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

        first_target_user_created = (
            after_first_user_match_count - before_user_match_count
        )

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

        second_target_user_created = (
            after_second_user_match_count - after_first_user_match_count
        )

        target_match = session.execute(
            select(TenderMatch).where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one_or_none()

        session.commit()

        if target_match is None:
            raise ValueError("expected target TenderMatch row was not created")

        if first_target_user_created != 1:
            raise ValueError(
                f"expected exactly one target user match on first run, got {first_target_user_created}"
            )

        if second_target_user_created != 0:
            raise ValueError(
                f"expected zero target user matches on second run, got {second_target_user_created}"
            )

        print(f"verify_match_email={unique_email}")
        print(f"verify_match_keyword={unique_marker}")
        print(f"verify_match_profile_keywords={profile.keywords}")
        print(f"verify_match_tender_ref={tender_ref}")
        print(f"verify_match_tender_id={tender.id}")
        print(f"verify_match_tender_created={tender_created}")
        print(f"verify_match_first_global_created={first_global_created}")
        print(f"verify_match_second_global_created={second_global_created}")
        print(f"verify_match_first_target_user_created={first_target_user_created}")
        print(f"verify_match_second_target_user_created={second_target_user_created}")
        print(f"verify_match_row_id={target_match.id}")
        print(f"verify_match_keywords={target_match.matched_keywords}")


if __name__ == "__main__":
    run()
