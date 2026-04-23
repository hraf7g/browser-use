from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from src.crawler.sources.saudi_etimad_crawler import (
    SaudiEtimadCrawlerError,
    run_saudi_etimad_crawl,
)
from src.crawler.sources.saudi_etimad_normalizer import (
    normalize_saudi_etimad_items,
)
from src.crawler.sources.saudi_etimad_quality import (
    assess_saudi_etimad_payloads,
)

SAUDI_ETIMAD_VERIFICATION_SOURCE_ID = UUID("44444444-4444-4444-4444-444444444444")


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Saudi Etimad quality layer.

    This script verifies:
    - live crawl execution succeeds
    - normalized rows can be quality-assessed
    - fallback issuing entities are flagged
        - missing closing-date rows are flagged
    - both higher-confidence and review-required examples are surfaced when available
    """
    crawl_result = await run_saudi_etimad_crawl()
    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled item, got zero")

    normalized_rows = normalize_saudi_etimad_items(
        source_id=SAUDI_ETIMAD_VERIFICATION_SOURCE_ID,
        items=crawl_result.items,
    )
    if not normalized_rows:
        raise ValueError("expected at least one normalized row, got zero")

    assessments = assess_saudi_etimad_payloads(normalized_rows)
    if not assessments:
        raise ValueError("expected at least one quality assessment, got zero")

    if len(assessments) != len(normalized_rows):
        raise ValueError("quality assessment count does not match normalized row count")

    missing_closing_date_flag_count = sum(
        1 for assessment in assessments if "closing_date_missing" in assessment.quality_flags
    )
    fallback_entity_flag_count = sum(
        1 for assessment in assessments if "issuing_entity_platform_fallback" in assessment.quality_flags
    )
    review_required_count = sum(
        1 for assessment in assessments if assessment.is_review_required
    )
    higher_confidence_count = sum(
        1 for assessment in assessments if not assessment.is_review_required
    )

    if missing_closing_date_flag_count < 1:
        raise ValueError("expected at least one missing closing-date flag, got zero")

    if fallback_entity_flag_count < 1:
        raise ValueError("expected at least one fallback issuing-entity flag, got zero")

    first_assessment = assessments[0]
    if first_assessment.payload.title != normalized_rows[0].title:
        raise ValueError("quality assessment mutated the payload title unexpectedly")

    print(f"verify_saudi_etimad_quality_source_name={crawl_result.source_name}")
    print(f"verify_saudi_etimad_quality_total_crawled_items={crawl_result.total_items}")
    print(f"verify_saudi_etimad_quality_total_normalized_rows={len(normalized_rows)}")
    print(f"verify_saudi_etimad_quality_total_assessments={len(assessments)}")
    print(f"verify_saudi_etimad_quality_review_required_count={review_required_count}")
    print(f"verify_saudi_etimad_quality_higher_confidence_count={higher_confidence_count}")
    print(f"verify_saudi_etimad_quality_missing_closing_date_flag_count={missing_closing_date_flag_count}")
    print(f"verify_saudi_etimad_quality_fallback_entity_flag_count={fallback_entity_flag_count}")
    print(f"verify_saudi_etimad_quality_first_title={first_assessment.payload.title}")
    print(f"verify_saudi_etimad_quality_first_tender_ref={first_assessment.payload.tender_ref}")
    print(f"verify_saudi_etimad_quality_first_score={first_assessment.quality_score}")
    print(
        "verify_saudi_etimad_quality_first_review_required="
        f"{first_assessment.is_review_required}"
    )
    print(f"verify_saudi_etimad_quality_first_flags={first_assessment.quality_flags}")

    higher_confidence_examples = [
        assessment for assessment in assessments if not assessment.is_review_required
    ][:3]
    review_required_examples = [
        assessment for assessment in assessments if assessment.is_review_required
    ][:5]

    for index, assessment in enumerate(higher_confidence_examples, start=1):
        print(f"higher_confidence_example_{index}_title={assessment.payload.title}")
        print(f"higher_confidence_example_{index}_score={assessment.quality_score}")
        print(f"higher_confidence_example_{index}_flags={assessment.quality_flags}")

    for index, assessment in enumerate(review_required_examples, start=1):
        print(f"review_required_example_{index}_title={assessment.payload.title}")
        print(f"review_required_example_{index}_score={assessment.quality_score}")
        print(f"review_required_example_{index}_flags={assessment.quality_flags}")


def run() -> None:
    """Synchronous module entrypoint."""
    try:
        asyncio.run(_run())
    except SaudiEtimadCrawlerError as exc:
        print(f"SAUDI_ETIMAD QUALITY VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
