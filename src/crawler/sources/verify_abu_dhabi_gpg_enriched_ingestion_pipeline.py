from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from src.crawler.sources.abu_dhabi_gpg_crawler import (
    AbuDhabiGPGCrawlerError,
    run_abu_dhabi_gpg_crawl,
)
from src.crawler.sources.abu_dhabi_gpg_detail_crawler import (
    AbuDhabiGPGDetailCrawlerError,
    run_abu_dhabi_gpg_detail_crawl,
)
from src.crawler.sources.abu_dhabi_gpg_enriched_normalizer import (
    normalize_abu_dhabi_gpg_enriched_items,
)
from src.crawler.sources.abu_dhabi_gpg_enriched_quality import (
    assess_abu_dhabi_gpg_enriched_payloads,
)
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.session import get_session_factory
from src.ingestion.tender_ingestion_service import ingest_tender

SOURCE_NAME = "Abu Dhabi GPG"


def _truncate(value: str, limit: int = 180) -> str:
    """Return a compact single-line preview for verification output."""
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the ADGPG enriched ingestion pipeline.

    This script verifies:
    - live widget crawl execution succeeds
    - live detail enrichment succeeds
    - enriched rows can be normalized and quality-assessed
    - accepted rows are ingested while review-required rows are excluded
    - ingested tenders have populated search_text
    - ingested tenders belong to the correct source
    - the transaction is rolled back so verification does not mutate persisted data
    """
    session_factory = get_session_factory()
    crawl_result = await run_abu_dhabi_gpg_crawl()
    detail_result = await run_abu_dhabi_gpg_detail_crawl()

    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled widget item, got zero")
    if detail_result.sample_count < 1:
        raise ValueError("expected at least one sampled detail item, got zero")

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

        normalized_rows = normalize_abu_dhabi_gpg_enriched_items(
            source_id=source.id,
            items=detail_result.items,
        )
        if not normalized_rows:
            raise ValueError("expected at least one enriched normalized row, got zero")

        assessments = assess_abu_dhabi_gpg_enriched_payloads(normalized_rows)
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
                "expected at least one accepted ADGPG enriched row, got zero"
            )

        for assessment in accepted_assessments:
            if assessment.payload.issuing_entity == SOURCE_NAME:
                raise ValueError(
                    "accepted enriched row still used the platform fallback issuing_entity"
                )
            if assessment.payload.tender_ref is None:
                raise ValueError(
                    "accepted enriched row still has missing tender_ref"
                )

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

        print(f"verify_pipeline_source_name={detail_result.source_name}")
        print(f"verify_pipeline_total_widget_crawled_rows={crawl_result.total_items}")
        print(f"verify_pipeline_total_detail_sampled_rows={detail_result.sample_count}")
        print(f"verify_pipeline_total_enriched_normalized_rows={len(normalized_rows)}")
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
    except (AbuDhabiGPGCrawlerError, AbuDhabiGPGDetailCrawlerError) as exc:
        print(
            f"ABU_DHABI_GPG ENRICHED INGESTION PIPELINE VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
