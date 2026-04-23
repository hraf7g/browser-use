from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from src.crawler.sources.saudi_misa_crawler import (
    SaudiMisaCrawlerError,
    run_saudi_misa_crawl,
)
from src.crawler.sources.saudi_misa_normalizer import normalize_saudi_misa_items
from src.crawler.sources.saudi_misa_quality import assess_saudi_misa_payloads
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender

SOURCE_NAME = "Saudi MISA Procurements"


def _truncate(value: str, limit: int = 180) -> str:
    """Return a compact single-line preview for verification output."""
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Saudi MISA ingestion pipeline.

    This script verifies:
    - live crawl execution succeeds
    - rows can be normalized
    - rows can be quality-assessed
    - accepted rows are ingested while review-required rows are excluded
    - ingested tenders have populated search_text
    - ingested tenders belong to the correct source
    - the transaction is rolled back so verification does not mutate persisted data
    """
    session_factory = get_session_factory()
    crawl_result = await run_saudi_misa_crawl()

    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled item, got zero")

    with session_factory() as session:
        source = session.execute(
            select(Source).where(Source.name == SOURCE_NAME)
        ).scalar_one_or_none()

        if source is None:
            raise ValueError(
                f"source '{SOURCE_NAME}' was not found; seed sources first"
            )

        before_count = len(
            session.execute(
                select(Tender).where(Tender.source_id == source.id)
            ).scalars().all()
        )

        normalized_rows = normalize_saudi_misa_items(
            source_id=source.id,
            items=crawl_result.items,
        )
        if not normalized_rows:
            raise ValueError("expected at least one normalized row, got zero")

        assessments = assess_saudi_misa_payloads(normalized_rows)
        if not assessments:
            raise ValueError("expected at least one quality assessment, got zero")

        accepted_assessments = [
            assessment for assessment in assessments if not assessment.is_review_required
        ]
        review_required_assessments = [
            assessment for assessment in assessments if assessment.is_review_required
        ]

        if not accepted_assessments:
            raise ValueError("expected at least one accepted Saudi MISA row, got zero")

        sample_accept_count = min(10, len(accepted_assessments))
        sample_accepts = accepted_assessments[:sample_accept_count]

        created_count = 0
        updated_count = 0
        ingested_tenders: list[Tender] = []

        for assessment in sample_accepts:
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
                raise ValueError("ingested tender source_id does not match expected source")
            if not tender.title.strip():
                raise ValueError("ingested tender title is unexpectedly empty")
            if not isinstance(tender.search_text, str) or not tender.search_text.strip():
                raise ValueError("ingested tender search_text is unexpectedly empty")

        after_count = len(
            session.execute(
                select(Tender).where(Tender.source_id == source.id)
            ).scalars().all()
        )

        first_accepted = sample_accepts[0].payload
        first_accepted_assessment = sample_accepts[0]
        first_ingested = ingested_tenders[0]

        print(f"verify_pipeline_source_name={crawl_result.source_name}")
        print(f"verify_pipeline_total_crawled_rows={crawl_result.total_items}")
        print(f"verify_pipeline_total_normalized_rows={len(normalized_rows)}")
        print(f"verify_pipeline_total_review_required={len(review_required_assessments)}")
        print(f"verify_pipeline_total_accepted={len(accepted_assessments)}")
        print(f"verify_pipeline_sample_accept_count={sample_accept_count}")
        print(f"verify_pipeline_created_count={created_count}")
        print(f"verify_pipeline_updated_count={updated_count}")
        print(f"verify_pipeline_before_count={before_count}")
        print(f"verify_pipeline_after_count={after_count}")
        print(f"verify_pipeline_first_accepted_title={first_accepted.title}")
        print(f"verify_pipeline_first_accepted_tender_ref={first_accepted.tender_ref}")
        print(f"verify_pipeline_first_accepted_category={first_accepted.category}")
        print(f"verify_pipeline_first_accepted_source_url={first_accepted.source_url}")
        print(
            "verify_pipeline_first_accepted_flags="
            f"{first_accepted_assessment.quality_flags}"
        )
        print(
            "verify_pipeline_first_ingested_search_text_preview="
            f"{_truncate(first_ingested.search_text)}"
        )

        session.rollback()


def run() -> None:
    """Synchronous module entrypoint."""
    try:
        asyncio.run(_run())
    except SaudiMisaCrawlerError as exc:
        print(
            f"SAUDI_MISA INGESTION PIPELINE VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
