from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from src.api.services.keyword_profile_service import upsert_keyword_profile
from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.models.tender_match import TenderMatch
from src.db.models.user import User
from src.db.seed_sources import seed_sources
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender
from src.notifications.notification_preference_service import (
    update_notification_preference,
)
from src.shared.config.settings import get_settings
from src.shared.schemas.keyword_profile import KeywordProfileUpsertRequest
from src.shared.schemas.notification_preference import (
    NotificationPreferenceUpdateRequest,
)
from src.shared.schemas.tender_ingestion import TenderIngestionInput
from src.shared.security.passwords import hash_password

SMOKE_SOURCE_NAME = 'Dubai eSupply'
SMOKE_USER_EMAIL = 'smoke-validation@example.com'
SMOKE_USER_PASSWORD = 'SmokeValidation123!'
SMOKE_SOURCE_URL = 'https://esupply.dubai.gov.ae'
SMOKE_TENDER_PATH = '/smoke-validation/tender-001'
SMOKE_TENDER_REF = 'SMOKE-TENDER-001'
SMOKE_TENDER_DEDUPE_KEY = 'smoke-validation-dubai-esupply-tender-001'
SMOKE_TENDER_TITLE = 'Smoke Validation Tender - SME Procurement Services'
SMOKE_TENDER_ENTITY = 'Dubai eSupply'
SMOKE_TENDER_CATEGORY = 'Procurement Services'
SMOKE_TENDER_SUMMARY = (
    'Stable smoke-validation tender used to verify list and detail paths for Tender Watch.'
)
SMOKE_MATCHED_KEYWORDS = ['procurement services', 'sme tender', 'dubai supply']
SMOKE_INDUSTRY_LABEL = 'SME Procurement'
SMOKE_RUN_IDENTIFIER = 'smoke-validation-run-001'


@dataclass(frozen=True)
class SmokeValidationDataset:
    """Stable local/staging dataset used for repeatable smoke validation."""

    source_id: UUID
    source_name: str
    user_id: UUID
    user_email: str
    user_password: str
    tender_id: UUID
    tender_ref: str
    tender_title: str
    tender_path: str
    crawl_run_id: UUID
    matched_keywords: list[str]


def ensure_smoke_validation_dataset() -> SmokeValidationDataset:
    """Create or refresh the explicit smoke-validation dataset."""
    _ensure_non_production_environment()
    seed_sources()

    session_factory = get_session_factory()
    now = datetime.now(UTC)

    with session_factory() as session:
        source = session.execute(
            select(Source).where(Source.name == SMOKE_SOURCE_NAME)
        ).scalar_one_or_none()
        if source is None:
            raise ValueError(
                f"source '{SMOKE_SOURCE_NAME}' was not found after seeding sources"
            )

        source.status = 'healthy'
        source.failure_count = 0
        source.last_failed_run_at = None
        source.last_successful_run_at = now - timedelta(minutes=2)

        user = session.execute(
            select(User).where(User.email == SMOKE_USER_EMAIL)
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=SMOKE_USER_EMAIL,
                password_hash=hash_password(SMOKE_USER_PASSWORD),
                is_active=True,
            )
            session.add(user)
            session.flush()
        else:
            user.password_hash = hash_password(SMOKE_USER_PASSWORD)
            user.is_active = True
            session.flush()

        upsert_keyword_profile(
            session=session,
            user_id=user.id,
            payload=KeywordProfileUpsertRequest(
                keywords=list(SMOKE_MATCHED_KEYWORDS),
                alert_enabled=True,
                industry_label=SMOKE_INDUSTRY_LABEL,
            ),
        )

        update_notification_preference(
            session=session,
            user_id=user.id,
            payload=NotificationPreferenceUpdateRequest(
                email_enabled=True,
                whatsapp_enabled=False,
                whatsapp_phone_e164=None,
                daily_brief_enabled=True,
                instant_alert_enabled=True,
                preferred_language='en',
            ),
        )

        tender, _ = ingest_tender(
            session=session,
            payload=TenderIngestionInput(
                source_id=source.id,
                source_url=f'{SMOKE_SOURCE_URL}{SMOKE_TENDER_PATH}',
                title=SMOKE_TENDER_TITLE,
                issuing_entity=SMOKE_TENDER_ENTITY,
                closing_date=now + timedelta(days=21),
                dedupe_key=SMOKE_TENDER_DEDUPE_KEY,
                tender_ref=SMOKE_TENDER_REF,
                opening_date=now - timedelta(days=2),
                published_at=now - timedelta(days=3),
                category=SMOKE_TENDER_CATEGORY,
                ai_summary=SMOKE_TENDER_SUMMARY,
            ),
        )

        crawl_run = session.execute(
            select(CrawlRun).where(CrawlRun.run_identifier == SMOKE_RUN_IDENTIFIER)
        ).scalar_one_or_none()
        if crawl_run is None:
            crawl_run = CrawlRun(
                source_id=source.id,
                status='success',
                started_at=now - timedelta(minutes=10),
                finished_at=now - timedelta(minutes=8),
                new_tenders_count=1,
                failure_reason=None,
                failure_step=None,
                run_identifier=SMOKE_RUN_IDENTIFIER,
            )
            session.add(crawl_run)
            session.flush()
        else:
            crawl_run.source_id = source.id
            crawl_run.status = 'success'
            crawl_run.started_at = now - timedelta(minutes=10)
            crawl_run.finished_at = now - timedelta(minutes=8)
            crawl_run.new_tenders_count = 1
            crawl_run.failure_reason = None
            crawl_run.failure_step = None
            session.flush()

        tender_match = session.execute(
            select(TenderMatch).where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one_or_none()
        if tender_match is None:
            tender_match = TenderMatch(
                user_id=user.id,
                tender_id=tender.id,
                matched_keywords=list(SMOKE_MATCHED_KEYWORDS),
                alerted_at=now - timedelta(minutes=6),
                sent_at=now - timedelta(minutes=5),
            )
            session.add(tender_match)
            session.flush()
        else:
            tender_match.matched_keywords = list(SMOKE_MATCHED_KEYWORDS)
            tender_match.alerted_at = now - timedelta(minutes=6)
            tender_match.sent_at = now - timedelta(minutes=5)
            session.flush()

        session.commit()

        return SmokeValidationDataset(
            source_id=source.id,
            source_name=source.name,
            user_id=user.id,
            user_email=user.email,
            user_password=SMOKE_USER_PASSWORD,
            tender_id=tender.id,
            tender_ref=tender.tender_ref or SMOKE_TENDER_REF,
            tender_title=tender.title,
            tender_path=f'/tenders/{tender.id}',
            crawl_run_id=crawl_run.id,
            matched_keywords=list(tender_match.matched_keywords or []),
        )


def get_smoke_validation_dataset() -> SmokeValidationDataset | None:
    """Load the smoke-validation dataset without mutating the database."""
    session_factory = get_session_factory()

    with session_factory() as session:
        user = session.execute(
            select(User).where(User.email == SMOKE_USER_EMAIL)
        ).scalar_one_or_none()
        if user is None:
            return None

        source = session.execute(
            select(Source).where(Source.name == SMOKE_SOURCE_NAME)
        ).scalar_one_or_none()
        if source is None:
            return None

        tender = session.execute(
            select(Tender).where(
                Tender.source_id == source.id,
                Tender.dedupe_key == SMOKE_TENDER_DEDUPE_KEY,
            )
        ).scalar_one_or_none()
        if tender is None:
            return None

        crawl_run = session.execute(
            select(CrawlRun).where(CrawlRun.run_identifier == SMOKE_RUN_IDENTIFIER)
        ).scalar_one_or_none()
        if crawl_run is None:
            return None

        tender_match = session.execute(
            select(TenderMatch).where(
                TenderMatch.user_id == user.id,
                TenderMatch.tender_id == tender.id,
            )
        ).scalar_one_or_none()
        if tender_match is None:
            return None

        return SmokeValidationDataset(
            source_id=source.id,
            source_name=source.name,
            user_id=user.id,
            user_email=user.email,
            user_password=SMOKE_USER_PASSWORD,
            tender_id=tender.id,
            tender_ref=tender.tender_ref or SMOKE_TENDER_REF,
            tender_title=tender.title,
            tender_path=f'/tenders/{tender.id}',
            crawl_run_id=crawl_run.id,
            matched_keywords=list(tender_match.matched_keywords or []),
        )


def describe_smoke_validation_dataset(dataset: SmokeValidationDataset) -> list[str]:
    """Return stable key=value lines for scripts and operators."""
    return [
        'smoke_validation_dataset_seeded=true',
        f'smoke_validation_source_name={dataset.source_name}',
        f'smoke_validation_source_id={dataset.source_id}',
        f'smoke_validation_user_email={dataset.user_email}',
        f'smoke_validation_user_id={dataset.user_id}',
        f'smoke_validation_user_password={dataset.user_password}',
        f'smoke_validation_tender_id={dataset.tender_id}',
        f'smoke_validation_tender_ref={dataset.tender_ref}',
        f'smoke_validation_tender_title={dataset.tender_title}',
        f'smoke_validation_tender_path={dataset.tender_path}',
        f'smoke_validation_crawl_run_id={dataset.crawl_run_id}',
        f'smoke_validation_matched_keywords={dataset.matched_keywords}',
    ]


def _ensure_non_production_environment() -> None:
    """Reject smoke-data writes in production."""
    settings = get_settings()
    if settings.environment == 'production':
        raise ValueError(
            'smoke validation data seeding is disabled in production environments'
        )

