from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from src.crawler.sources.abu_dhabi_gpg_crawler import (
    AbuDhabiGPGCrawlerError,
    run_abu_dhabi_gpg_crawl,
)
from src.crawler.sources.abu_dhabi_gpg_normalizer import (
    normalize_abu_dhabi_gpg_items,
)
from src.crawler.sources.abu_dhabi_gpg_quality import (
    assess_abu_dhabi_gpg_payloads,
)

ABU_DHABI_GPG_VERIFICATION_SOURCE_ID = UUID("88888888-8888-8888-8888-888888888888")


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the Abu Dhabi GPG quality layer.

    This script verifies:
    - live crawl execution succeeds
    - normalized rows can be quality-assessed
    - issuing_entity fallback is flagged
    - missing tender_ref is flagged
    - missing published_at is flagged
    - generic homepage-widget category is flagged when applicable
    - higher-confidence examples are shown only if the live data actually allows them
    """
    crawl_result = await run_abu_dhabi_gpg_crawl()
    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled item, got zero")

    normalized_rows = normalize_abu_dhabi_gpg_items(
        source_id=ABU_DHABI_GPG_VERIFICATION_SOURCE_ID,
        items=crawl_result.items,
    )
    if not normalized_rows:
        raise ValueError("expected at least one normalized row, got zero")

    assessments = assess_abu_dhabi_gpg_payloads(normalized_rows)
    if not assessments:
        raise ValueError("expected at least one quality assessment, got zero")

    if len(assessments) != len(normalized_rows):
        raise ValueError("quality assessment count does not match normalized row count")

    issuing_entity_fallback_flag_count = sum(
        1
        for assessment in assessments
        if "issuing_entity_platform_fallback" in assessment.quality_flags
    )
    tender_ref_missing_flag_count = sum(
        1 for assessment in assessments if "tender_ref_missing" in assessment.quality_flags
    )
    published_missing_flag_count = sum(
        1 for assessment in assessments if "published_at_missing" in assessment.quality_flags
    )
    generic_category_flag_count = sum(
        1
        for assessment in assessments
        if "category_generic_widget_label" in assessment.quality_flags
    )
    review_required_count = sum(
        1 for assessment in assessments if assessment.is_review_required
    )
    higher_confidence_count = sum(
        1 for assessment in assessments if not assessment.is_review_required
    )

    if issuing_entity_fallback_flag_count < 1:
        raise ValueError("expected at least one issuing_entity fallback flag, got zero")
    if tender_ref_missing_flag_count < 1:
        raise ValueError("expected at least one missing tender_ref flag, got zero")
    if published_missing_flag_count < 1:
        raise ValueError("expected at least one missing published_at flag, got zero")
    if generic_category_flag_count < 1:
        raise ValueError("expected at least one generic category flag, got zero")

    first_assessment = assessments[0]
    if first_assessment.payload.title != normalized_rows[0].title:
        raise ValueError("quality assessment mutated the payload title unexpectedly")

    print(f"verify_abu_dhabi_gpg_quality_source_name={crawl_result.source_name}")
    print(f"verify_abu_dhabi_gpg_quality_total_crawled_items={crawl_result.total_items}")
    print(
        f"verify_abu_dhabi_gpg_quality_total_normalized_rows={len(normalized_rows)}"
    )
    print(f"verify_abu_dhabi_gpg_quality_total_assessments={len(assessments)}")
    print(
        f"verify_abu_dhabi_gpg_quality_review_required_count={review_required_count}"
    )
    print(
        "verify_abu_dhabi_gpg_quality_higher_confidence_count="
        f"{higher_confidence_count}"
    )
    print(
        "verify_abu_dhabi_gpg_quality_fallback_entity_flag_count="
        f"{issuing_entity_fallback_flag_count}"
    )
    print(
        "verify_abu_dhabi_gpg_quality_tender_ref_missing_flag_count="
        f"{tender_ref_missing_flag_count}"
    )
    print(
        "verify_abu_dhabi_gpg_quality_published_missing_flag_count="
        f"{published_missing_flag_count}"
    )
    print(
        "verify_abu_dhabi_gpg_quality_generic_category_flag_count="
        f"{generic_category_flag_count}"
    )
    print(f"verify_abu_dhabi_gpg_quality_first_title={first_assessment.payload.title}")
    print(
        f"verify_abu_dhabi_gpg_quality_first_tender_ref={first_assessment.payload.tender_ref}"
    )
    print(
        f"verify_abu_dhabi_gpg_quality_first_score={first_assessment.quality_score}"
    )
    print(
        "verify_abu_dhabi_gpg_quality_first_review_required="
        f"{first_assessment.is_review_required}"
    )
    print(
        f"verify_abu_dhabi_gpg_quality_first_flags={first_assessment.quality_flags}"
    )

    higher_confidence_examples = [
        assessment for assessment in assessments if not assessment.is_review_required
    ][:3]
    review_required_examples = [
        assessment for assessment in assessments if assessment.is_review_required
    ][:5]

    print(
        "verify_abu_dhabi_gpg_quality_higher_confidence_examples_available="
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
    except AbuDhabiGPGCrawlerError as exc:
        print(
            f"ABU_DHABI_GPG QUALITY VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
