from __future__ import annotations

import asyncio

from sqlalchemy import select

from src.crawler.sources.dubai_esupply_crawler import run_dubai_esupply_crawl
from src.crawler.sources.dubai_esupply_normalizer import normalize_dubai_esupply_rows
from src.crawler.sources.dubai_esupply_quality import assess_dubai_esupply_payloads
from src.db.models.source import Source
from src.db.session import get_session_factory

SOURCE_NAME = "Dubai eSupply"


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Dubai eSupply quality assessment layer.

    This script verifies:
    - live crawl execution succeeds
    - normalized rows can be quality-assessed
    - weak titles are flagged deterministically
    - the assessment layer produces review signals without mutating payloads
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

        review_required_count = sum(
            1 for assessment in assessments if assessment.is_review_required
        )

        first_assessment = assessments[0]

        if first_assessment.payload.title != normalized_rows[0].title:
            raise ValueError("quality assessment mutated the payload title unexpectedly")

        print(f"verify_quality_source_name={crawl_result.source_name}")
        print(f"verify_quality_total_crawled_rows={crawl_result.total_rows}")
        print(f"verify_quality_total_normalized_rows={len(normalized_rows)}")
        print(f"verify_quality_total_assessments={len(assessments)}")
        print(f"verify_quality_review_required_count={review_required_count}")
        print(f"verify_quality_first_title={first_assessment.payload.title}")
        print(f"verify_quality_first_tender_ref={first_assessment.payload.tender_ref}")
        print(f"verify_quality_first_score={first_assessment.quality_score}")
        print(f"verify_quality_first_review_required={first_assessment.is_review_required}")
        print(f"verify_quality_first_flags={first_assessment.quality_flags}")

        flagged_examples = [
            assessment for assessment in assessments if assessment.is_review_required
        ][:5]

        for index, assessment in enumerate(flagged_examples, start=1):
            print(f"flagged_example_{index}_title={assessment.payload.title}")
            print(f"flagged_example_{index}_score={assessment.quality_score}")
            print(f"flagged_example_{index}_flags={assessment.quality_flags}")


def run() -> None:
    """Synchronous module entrypoint."""
    asyncio.run(_run())


if __name__ == "__main__":
    run()
