from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from src.crawler.sources.bahrain_tender_board_crawler import (
    BahrainTenderBoardCrawlerError,
    run_bahrain_tender_board_crawl,
)
from src.crawler.sources.bahrain_tender_board_normalizer import (
    normalize_bahrain_tender_board_items,
)
from src.crawler.sources.bahrain_tender_board_quality import (
    assess_bahrain_tender_board_payloads,
)

BAHRAIN_TENDER_BOARD_VERIFICATION_SOURCE_ID = UUID(
    "55555555-5555-5555-5555-555555555555"
)


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Bahrain Tender Board quality layer.

    This script verifies:
    - live crawl execution succeeds
    - normalized rows can be quality-assessed
    - missing closing-date rows are flagged
    - missing publication date is flagged
    - review-required examples are surfaced
    - higher-confidence examples are shown only if the live data actually allows them
    """
    crawl_result = await run_bahrain_tender_board_crawl()
    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled item, got zero")

    normalized_rows = normalize_bahrain_tender_board_items(
        source_id=BAHRAIN_TENDER_BOARD_VERIFICATION_SOURCE_ID,
        items=crawl_result.items,
    )
    if not normalized_rows:
        raise ValueError("expected at least one normalized row, got zero")

    assessments = assess_bahrain_tender_board_payloads(normalized_rows)
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
    review_required_count = sum(
        1 for assessment in assessments if assessment.is_review_required
    )
    higher_confidence_count = sum(
        1 for assessment in assessments if not assessment.is_review_required
    )

    if missing_closing_date_flag_count < 1:
        raise ValueError("expected at least one missing closing-date flag, got zero")

    if published_missing_flag_count < 1:
        raise ValueError("expected at least one missing published_at flag, got zero")

    if review_required_count < 1:
        raise ValueError("expected at least one review-required assessment, got zero")

    first_assessment = assessments[0]
    if first_assessment.payload.title != normalized_rows[0].title:
        raise ValueError("quality assessment mutated the payload title unexpectedly")

    print(f"verify_bahrain_tender_board_quality_source_name={crawl_result.source_name}")
    print(
        f"verify_bahrain_tender_board_quality_total_crawled_items={crawl_result.total_items}"
    )
    print(
        "verify_bahrain_tender_board_quality_total_normalized_rows="
        f"{len(normalized_rows)}"
    )
    print(
        f"verify_bahrain_tender_board_quality_total_assessments={len(assessments)}"
    )
    print(
        "verify_bahrain_tender_board_quality_review_required_count="
        f"{review_required_count}"
    )
    print(
        "verify_bahrain_tender_board_quality_higher_confidence_count="
        f"{higher_confidence_count}"
    )
    print(
        "verify_bahrain_tender_board_quality_missing_closing_date_flag_count="
        f"{missing_closing_date_flag_count}"
    )
    print(
        "verify_bahrain_tender_board_quality_published_missing_flag_count="
        f"{published_missing_flag_count}"
    )
    print(f"verify_bahrain_tender_board_quality_first_title={first_assessment.payload.title}")
    print(
        "verify_bahrain_tender_board_quality_first_tender_ref="
        f"{first_assessment.payload.tender_ref}"
    )
    print(
        "verify_bahrain_tender_board_quality_first_score="
        f"{first_assessment.quality_score}"
    )
    print(
        "verify_bahrain_tender_board_quality_first_review_required="
        f"{first_assessment.is_review_required}"
    )
    print(
        "verify_bahrain_tender_board_quality_first_flags="
        f"{first_assessment.quality_flags}"
    )

    higher_confidence_examples = [
        assessment for assessment in assessments if not assessment.is_review_required
    ][:3]
    review_required_examples = [
        assessment for assessment in assessments if assessment.is_review_required
    ][:5]

    print(
        "verify_bahrain_tender_board_quality_higher_confidence_examples_available="
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
    except BahrainTenderBoardCrawlerError as exc:
        print(
            f"BAHRAIN_TENDER_BOARD QUALITY VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
