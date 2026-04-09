from __future__ import annotations

import asyncio

from sqlalchemy import select

from src.crawler.sources.dubai_esupply_crawler import run_dubai_esupply_crawl
from src.crawler.sources.dubai_esupply_normalizer import normalize_dubai_esupply_rows
from src.crawler.sources.dubai_esupply_quality import assess_dubai_esupply_payloads
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender

SOURCE_NAME = "Dubai eSupply"


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Dubai eSupply ingestion pipeline.

    This script verifies:
    - live crawl execution succeeds
    - rows can be normalized
    - rows can be quality-assessed
    - non-review rows can be ingested successfully
    - the transaction is rolled back so verification does not mutate production data
    """
    session_factory = get_session_factory()
    crawl_result = await run_dubai_esupply_crawl()

    if crawl_result.total_rows < 1:
        raise ValueError("expected at least one crawled row, got zero")

    with session_factory() as session:
        source = session.execute(
            select(Source).where(Source.name == SOURCE_NAME)
        ).scalar_one_or_none()

        if source is None:
            raise ValueError(
                f"source '{SOURCE_NAME}' was not found; seed sources first"
            )

        normalized_rows = normalize_dubai_esupply_rows(
            source_id=source.id,
            rows=crawl_result.rows,
        )

        if not normalized_rows:
            raise ValueError("expected at least one normalized row, got zero")

        assessments = assess_dubai_esupply_payloads(normalized_rows)

        if not assessments:
            raise ValueError("expected at least one quality assessment, got zero")

        accepted_assessments = [
            assessment for assessment in assessments if not assessment.is_review_required
        ]
        review_required_assessments = [
            assessment for assessment in assessments if assessment.is_review_required
        ]

        if not accepted_assessments:
            raise ValueError(
                "expected at least one non-review row for ingestion verification, got zero"
            )

        created_count = 0
        updated_count = 0

        before_tender_count = session.execute(
            select(Tender).where(Tender.source_id == source.id)
        ).scalars().all()
        before_count = len(before_tender_count)

        sample_accept_count = min(10, len(accepted_assessments))
        sample_accepts = accepted_assessments[:sample_accept_count]

        for assessment in sample_accepts:
            tender, created = ingest_tender(
                session=session,
                payload=assessment.payload,
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

            if tender.source_id != source.id:
                raise ValueError("ingested tender source_id does not match expected source")

            if not tender.title.strip():
                raise ValueError("ingested tender title is unexpectedly empty")

        after_tender_count = session.execute(
            select(Tender).where(Tender.source_id == source.id)
        ).scalars().all()
        after_count = len(after_tender_count)

        print(f"verify_pipeline_source_name={crawl_result.source_name}")
        print(f"verify_pipeline_total_crawled_rows={crawl_result.total_rows}")
        print(f"verify_pipeline_total_normalized_rows={len(normalized_rows)}")
        print(f"verify_pipeline_total_review_required={len(review_required_assessments)}")
        print(f"verify_pipeline_total_accepted={len(accepted_assessments)}")
        print(f"verify_pipeline_sample_accept_count={sample_accept_count}")
        print(f"verify_pipeline_created_count={created_count}")
        print(f"verify_pipeline_updated_count={updated_count}")
        print(f"verify_pipeline_before_count={before_count}")
        print(f"verify_pipeline_after_count={after_count}")

        first_accepted = sample_accepts[0].payload
        print(f"verify_pipeline_first_accepted_title={first_accepted.title}")
        print(f"verify_pipeline_first_accepted_tender_ref={first_accepted.tender_ref}")
        print(f"verify_pipeline_first_accepted_category={first_accepted.category}")
        print(f"verify_pipeline_first_accepted_closing_date={first_accepted.closing_date.isoformat()}")

        session.rollback()


def run() -> None:
    """Synchronous module entrypoint."""
    asyncio.run(_run())


if __name__ == "__main__":
    run()
