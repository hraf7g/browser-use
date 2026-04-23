from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from src.crawler.sources.saudi_misa_crawler import (
    SaudiMisaCrawlerError,
    run_saudi_misa_crawl,
)
from src.crawler.sources.saudi_misa_normalizer import normalize_saudi_misa_items
from src.crawler.sources.saudi_misa_quality import assess_saudi_misa_payloads

SAUDI_MISA_VERIFICATION_SOURCE_ID = UUID("77777777-7777-7777-7777-777777777777")


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Saudi MISA quality layer.

    This script verifies:
    - live crawl execution succeeds
    - normalized rows can be quality-assessed
        - missing closing-date rows are flagged
    - higher-confidence rows are surfaced when the stronger table allows them
    - review-required examples are surfaced when incomplete rows remain
    - higher-confidence examples are shown only if the live data actually allows them
    """
    crawl_result = await run_saudi_misa_crawl()
    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled item, got zero")

    normalized_rows = normalize_saudi_misa_items(
        source_id=SAUDI_MISA_VERIFICATION_SOURCE_ID,
        items=crawl_result.items,
    )
    if not normalized_rows:
        raise ValueError("expected at least one normalized row, got zero")

    assessments = assess_saudi_misa_payloads(normalized_rows)
    if not assessments:
        raise ValueError("expected at least one quality assessment, got zero")

    if len(assessments) != len(normalized_rows):
        raise ValueError("quality assessment count does not match normalized row count")

    missing_closing_date_flag_count = sum(
        1
        for assessment in assessments
        if "closing_date_missing" in assessment.quality_flags
    )
    published_missing_flag_count = sum(
        1
        for assessment in assessments
        if "published_at_missing" in assessment.quality_flags
    )
    category_missing_flag_count = sum(
        1
        for assessment in assessments
        if "category_missing" in assessment.quality_flags
    )
    review_required_count = sum(
        1 for assessment in assessments if assessment.is_review_required
    )
    higher_confidence_count = sum(
        1 for assessment in assessments if not assessment.is_review_required
    )

    if missing_closing_date_flag_count < 1:
        raise ValueError("expected at least one missing closing-date flag, got zero")

    if review_required_count < 1 and higher_confidence_count < 1:
        raise ValueError("expected at least one assessed row outcome, got none")

    first_assessment = assessments[0]
    if first_assessment.payload.title != normalized_rows[0].title:
        raise ValueError("quality assessment mutated the payload title unexpectedly")

    print(f"verify_saudi_misa_quality_source_name={crawl_result.source_name}")
    print(f"verify_saudi_misa_quality_total_crawled_items={crawl_result.total_items}")
    print(
        "verify_saudi_misa_quality_total_normalized_rows="
        f"{len(normalized_rows)}"
    )
    print(f"verify_saudi_misa_quality_total_assessments={len(assessments)}")
    print(
        "verify_saudi_misa_quality_review_required_count="
        f"{review_required_count}"
    )
    print(
        "verify_saudi_misa_quality_higher_confidence_count="
        f"{higher_confidence_count}"
    )
    print(
        "verify_saudi_misa_quality_missing_closing_date_flag_count="
        f"{missing_closing_date_flag_count}"
    )
    print(
        "verify_saudi_misa_quality_category_missing_flag_count="
        f"{category_missing_flag_count}"
    )
    print(
        "verify_saudi_misa_quality_published_missing_flag_count="
        f"{published_missing_flag_count}"
    )
    print(f"verify_saudi_misa_quality_first_title={first_assessment.payload.title}")
    print(
        "verify_saudi_misa_quality_first_tender_ref="
        f"{first_assessment.payload.tender_ref}"
    )
    print(
        "verify_saudi_misa_quality_first_score="
        f"{first_assessment.quality_score}"
    )
    print(
        "verify_saudi_misa_quality_first_review_required="
        f"{first_assessment.is_review_required}"
    )
    print(
        "verify_saudi_misa_quality_first_flags="
        f"{first_assessment.quality_flags}"
    )

    higher_confidence_examples = [
        assessment for assessment in assessments if not assessment.is_review_required
    ][:3]
    review_required_examples = [
        assessment for assessment in assessments if assessment.is_review_required
    ][:5]

    print(
        "verify_saudi_misa_quality_higher_confidence_examples_available="
        f"{bool(higher_confidence_examples)}"
    )

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
    except SaudiMisaCrawlerError as exc:
        print(f"SAUDI_MISA QUALITY VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
