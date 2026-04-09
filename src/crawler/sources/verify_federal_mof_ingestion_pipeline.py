from __future__ import annotations

import asyncio

from sqlalchemy import select

from src.crawler.sources.federal_mof_crawler import run_federal_mof_crawl
from src.crawler.sources.federal_mof_normalizer import normalize_federal_mof_rows
from src.crawler.sources.federal_mof_quality import assess_federal_mof_batch_quality
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender

SOURCE_NAME = "Federal MOF"


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Federal MOF
    ingestion pipeline.

    This script verifies:
    - live crawl execution succeeds
    - rows can be normalized
    - rows can be quality-assessed
    - accepted rows are ingested while review-required rows are excluded
    - ingested tenders have populated search_text
    - the transaction is rolled back so verification does not mutate persisted data
    """
    session_factory = get_session_factory()
    crawl_result = await run_federal_mof_crawl()

    if crawl_result.total_table_rows < 1:
        raise ValueError("expected at least one crawled table row, got zero")

    with session_factory() as session:
        source = session.execute(
            select(Source).where(Source.name == SOURCE_NAME)
        ).scalar_one_or_none()

        if source is None:
            raise ValueError(
                f"source '{SOURCE_NAME}' was not found; seed sources first"
            )

        before_tender_count = len(
            session.execute(
                select(Tender).where(Tender.source_id == source.id)
            ).scalars().all()
        )

        normalized_rows = normalize_federal_mof_rows(
            source_id=source.id,
            rows=crawl_result.table_rows,
        )
        if not normalized_rows:
            raise ValueError("expected at least one normalized row, got zero")

        assessments = assess_federal_mof_batch_quality(normalized_rows)
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
                "expected at least one accepted Federal MOF row, got zero"
            )

        created_count = 0
        updated_count = 0
        ingested_tenders: list[Tender] = []

        for assessment in accepted_assessments:
            tender, created = ingest_tender(
                session=session,
                payload=assessment.payload,
            )
            ingested_tenders.append(tender)

            if created:
                created_count += 1
            else:
                updated_count += 1

            if tender.source_id != source.id:
                raise ValueError("ingested tender source_id does not match source")

            if not tender.title.strip():
                raise ValueError("ingested tender title is unexpectedly empty")

            if not isinstance(tender.search_text, str) or not tender.search_text.strip():
                raise ValueError("ingested tender search_text is unexpectedly empty")

        after_tender_count = len(
            session.execute(
                select(Tender).where(Tender.source_id == source.id)
            ).scalars().all()
        )

        populated_search_text_count = sum(
            1
            for tender in ingested_tenders
            if isinstance(tender.search_text, str) and tender.search_text.strip()
        )

        first_accepted = accepted_assessments[0].payload

        print(f"verify_pipeline_source_name={crawl_result.source_name}")
        print(f"verify_pipeline_total_crawled_rows={crawl_result.total_table_rows}")
        print(f"verify_pipeline_total_normalized_rows={len(normalized_rows)}")
        print(f"verify_pipeline_total_review_required={len(review_required_assessments)}")
        print(f"verify_pipeline_total_accepted={len(accepted_assessments)}")
        print(f"verify_pipeline_created_count={created_count}")
        print(f"verify_pipeline_updated_count={updated_count}")
        print(f"verify_pipeline_before_count={before_tender_count}")
        print(f"verify_pipeline_after_count={after_tender_count}")
        print(f"verify_pipeline_populated_search_text_count={populated_search_text_count}")
        print(f"verify_pipeline_first_accepted_title={first_accepted.title}")
        print(f"verify_pipeline_first_accepted_tender_ref={first_accepted.tender_ref}")
        print(
            "verify_pipeline_first_accepted_closing_date="
            f"{first_accepted.closing_date.isoformat()}"
        )

        session.rollback()


def run() -> None:
    """Synchronous module entrypoint."""
    asyncio.run(_run())


if __name__ == "__main__":
    run()
