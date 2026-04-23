from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from src.db.models.source import Source
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender
from src.shared.schemas.tender_ingestion import TenderIngestionInput

MANUAL_SOURCE_NAME = "Dubai eSupply"


def run() -> None:
    """Insert or upsert one manual tender through the ingestion service."""
    session_factory = get_session_factory()

    with session_factory() as session:
        source = session.execute(
            select(Source).where(Source.name == MANUAL_SOURCE_NAME)
        ).scalar_one_or_none()

        if source is None:
            raise ValueError(
                f"source '{MANUAL_SOURCE_NAME}' was not found; seed sources first"
            )

        payload = TenderIngestionInput(
            source_id=source.id,
            source_url="https://esupply.dubai.gov.ae/manual-test-tender",
            title="Manual Test Tender - IT Support Services",
            issuing_entity="Dubai eSupply",
            closing_date=datetime(2026, 4, 30, 12, 0, tzinfo=timezone.utc),
            dedupe_key="manual-test-dubai-esupply-it-support-services-2026-04-30",
            tender_ref="MANUAL-TEST-001",
            opening_date=datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc),
            published_at=datetime(2026, 4, 6, 9, 0, tzinfo=timezone.utc),
            category="IT",
            ai_summary=None,
        )

        tender, created = ingest_tender(session=session, payload=payload)
        session.commit()

        print(f"manual_ingest_created={created}")
        print(f"manual_ingest_tender_id={tender.id}")
        print(f"manual_ingest_tender_ref={tender.tender_ref}")
        print(f"manual_ingest_title={tender.title}")


if __name__ == "__main__":
    run()
