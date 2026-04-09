from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select

from src.api.services.auth_service import register_user
from src.api.services.keyword_profile_service import upsert_keyword_profile
from src.db.models.email_delivery import EmailDelivery
from src.db.models.source import Source
from src.db.models.tender_match import TenderMatch
from src.db.session import get_session_factory
from src.email.daily_brief_dispatch_service import dispatch_daily_brief_for_user
from src.email.dev_email_backend import DEFAULT_DEV_OUTBOX_DIR
from src.ingestion.tender_ingestion_service import ingest_tender
from src.matching.tender_matching_service import match_tender_by_id
from src.shared.schemas.auth import SignupRequest
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest
from src.shared.schemas.tender_ingestion import TenderIngestionInput

SOURCE_NAME = "Dubai eSupply"
TEST_PASSWORD = "StrongPass123!"


def run() -> None:
    """
    Perform an isolated production-grade verification of the daily brief dispatch service.

    This script verifies:
    - a unique user can be created
    - a unique tender can be ingested and matched
    - a daily brief can be dispatched through the dev backend
    - one EmailDelivery row is created
    - included TenderMatch rows are marked sent
    - rerunning dispatch does not resend the same matches
    """
    session_factory = get_session_factory()
    unique_marker = f"utw-dispatch-{uuid4().hex}"
    unique_email = f"{unique_marker}@example.com"
    tender_ref = f"VERIFY-DISPATCH-{uuid4().hex[:12].upper()}"
    outbox_dir = DEFAULT_DEV_OUTBOX_DIR / unique_marker

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
                title=unique_marker,
                issuing_entity=f"verification-{unique_marker}",
                closing_date=datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
                dedupe_key=f"{unique_marker}-dedupe",
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

        after_user_match_count = session.execute(
            select(func.count())
            .select_from(TenderMatch)
            .where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one()

        first_target_user_created = after_user_match_count - before_user_match_count
        if first_target_user_created != 1:
            raise ValueError(
                f"expected exactly one new target-user match, got {first_target_user_created}"
            )

        dispatch_result = dispatch_daily_brief_for_user(
            session=session,
            user_id=user.id,
            outbox_dir=outbox_dir,
        )

        if dispatch_result is None:
            raise ValueError("expected dispatch result, got None")

        session.commit()

        email_delivery = session.get(EmailDelivery, dispatch_result.email_delivery_id)
        if email_delivery is None:
            raise ValueError("expected EmailDelivery row was not created")

        if email_delivery.user_id != user.id:
            raise ValueError("EmailDelivery user_id does not match expected user")

        if email_delivery.delivery_type != "daily_brief":
            raise ValueError(
                f"expected delivery_type 'daily_brief', got {email_delivery.delivery_type}"
            )

        if email_delivery.status != "sent":
            raise ValueError(
                f"expected delivery status 'sent', got {email_delivery.status}"
            )

        if email_delivery.match_count != 1:
            raise ValueError(
                f"expected EmailDelivery.match_count to be 1, got {email_delivery.match_count}"
            )

        if email_delivery.sent_at is None:
            raise ValueError("expected EmailDelivery.sent_at to be populated")

        tender_match = session.execute(
            select(TenderMatch).where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one_or_none()

        if tender_match is None:
            raise ValueError("expected TenderMatch row was not found after dispatch")

        if tender_match.sent_at is None:
            raise ValueError("expected TenderMatch.sent_at to be populated after dispatch")

        if not dispatch_result.output_path.exists():
            raise ValueError("expected dev outbox email file to exist after dispatch")

        rerun_result = dispatch_daily_brief_for_user(
            session=session,
            user_id=user.id,
            outbox_dir=outbox_dir,
        )

        if rerun_result is not None:
            raise ValueError("expected rerun dispatch to return None after matches were sent")

        print(f"verify_dispatch_email={unique_email}")
        print(f"verify_dispatch_keyword={unique_marker}")
        print(f"verify_dispatch_profile_keywords={profile.keywords}")
        print(f"verify_dispatch_tender_ref={tender_ref}")
        print(f"verify_dispatch_tender_id={tender.id}")
        print(f"verify_dispatch_tender_created={tender_created}")
        print(f"verify_dispatch_first_global_created={first_global_created}")
        print(f"verify_dispatch_first_target_user_created={first_target_user_created}")
        print(f"verify_dispatch_match_id={tender_match.id}")
        print(f"verify_dispatch_match_sent_at={tender_match.sent_at.isoformat()}")
        print(f"verify_dispatch_email_delivery_id={email_delivery.id}")
        print(f"verify_dispatch_email_delivery_status={email_delivery.status}")
        print(f"verify_dispatch_email_delivery_match_count={email_delivery.match_count}")
        print(f"verify_dispatch_output_path={dispatch_result.output_path}")
        print(f"verify_dispatch_backend_message_id={dispatch_result.backend_message_id}")
        print(f"verify_dispatch_rerun_result={rerun_result}")


if __name__ == "__main__":
    run()
