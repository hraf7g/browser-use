from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select

from src.api.services.auth_service import register_user
from src.api.services.keyword_profile_service import upsert_keyword_profile
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.matching.tender_matching_service import match_tender_by_id
from src.shared.schemas.auth import SignupRequest
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest

MANUAL_TENDER_REF = "MANUAL-TEST-001"
TEST_PASSWORD = "StrongPass123!"


def run() -> None:
    """Create a fresh user/profile and verify tender matching end to end."""
    session_factory = get_session_factory()

    with session_factory() as session:
        tender = session.execute(
            select(Tender).where(Tender.tender_ref == MANUAL_TENDER_REF)
        ).scalar_one_or_none()

        if tender is None:
            raise ValueError(
                f"tender '{MANUAL_TENDER_REF}' was not found; run manual ingestion first"
            )

        email = f"manual_match_{uuid4().hex}@example.com"

        user = register_user(
            session=session,
            payload=SignupRequest(
                email=email,
                password=TEST_PASSWORD,
            ),
        )

        profile = upsert_keyword_profile(
            session=session,
            user_id=user.id,
            payload=KeywordProfileUpsertRequest(
                keywords=["IT", "Support", "Services"],
                alert_enabled=True,
                industry_label="Technology",
            ),
        )

        first_created = match_tender_by_id(
            session=session,
            tender_id=tender.id,
        )
        second_created = match_tender_by_id(
            session=session,
            tender_id=tender.id,
        )

        tender_match = session.execute(
            select(TenderMatch).where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one_or_none()

        session.commit()

        if tender_match is None:
            raise ValueError("expected TenderMatch row was not created")

        print(f"manual_match_email={email}")
        print(f"manual_match_user_id={user.id}")
        print(f"manual_match_profile_keywords={profile.keywords}")
        print(f"manual_match_tender_id={tender.id}")
        print(f"manual_match_first_created={first_created}")
        print(f"manual_match_second_created={second_created}")
        print(f"manual_match_row_id={tender_match.id}")
        print(f"manual_match_keywords={tender_match.matched_keywords}")


if __name__ == "__main__":
    run()
