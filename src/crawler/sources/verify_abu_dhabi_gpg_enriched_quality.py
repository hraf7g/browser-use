from __future__ import annotations

import asyncio
import sys
from uuid import UUID

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
from src.crawler.sources.abu_dhabi_gpg_normalizer import (
    normalize_abu_dhabi_gpg_items,
)
from src.crawler.sources.abu_dhabi_gpg_quality import (
    assess_abu_dhabi_gpg_payloads,
)

ABU_DHABI_GPG_VERIFICATION_SOURCE_ID = UUID("88888888-8888-8888-8888-888888888888")


async def _run() -> None:
    """
    Perform an isolated production-grade verification of the enriched ADGPG quality layer.

    This script verifies:
    - live widget crawl execution succeeds
    - detail enrichment succeeds
    - enriched rows can be quality-assessed
    - issuing_entity fallback usage drops versus widget-only quality
    - missing tender_ref usage drops versus widget-only quality
    - higher-confidence and review-required counts are reported honestly
    """
    crawl_result = await run_abu_dhabi_gpg_crawl()
    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled widget item, got zero")

    detail_result = await run_abu_dhabi_gpg_detail_crawl()
    if detail_result.sample_count < 1:
        raise ValueError("expected at least one sampled detail item, got zero")

    widget_rows = normalize_abu_dhabi_gpg_items(
        source_id=ABU_DHABI_GPG_VERIFICATION_SOURCE_ID,
        items=crawl_result.items[: detail_result.sample_count],
    )
    enriched_rows = normalize_abu_dhabi_gpg_enriched_items(
        source_id=ABU_DHABI_GPG_VERIFICATION_SOURCE_ID,
        items=detail_result.items,
    )

    widget_assessments = assess_abu_dhabi_gpg_payloads(widget_rows)
    enriched_assessments = assess_abu_dhabi_gpg_enriched_payloads(enriched_rows)

    if len(enriched_assessments) != len(enriched_rows):
        raise ValueError("enriched assessment count does not match enriched row count")

    widget_fallback_flag_count = sum(
        1
        for assessment in widget_assessments
        if "issuing_entity_platform_fallback" in assessment.quality_flags
    )
    enriched_fallback_flag_count = sum(
        1
        for assessment in enriched_assessments
        if "issuing_entity_platform_fallback" in assessment.quality_flags
    )
    widget_tender_ref_missing_flag_count = sum(
        1 for assessment in widget_assessments if "tender_ref_missing" in assessment.quality_flags
    )
    enriched_tender_ref_missing_flag_count = sum(
        1
        for assessment in enriched_assessments
        if "tender_ref_missing" in assessment.quality_flags
    )
    published_missing_flag_count = sum(
        1
        for assessment in enriched_assessments
        if "published_at_missing" in assessment.quality_flags
    )
    review_required_count = sum(
        1 for assessment in enriched_assessments if assessment.is_review_required
    )
    higher_confidence_count = sum(
        1 for assessment in enriched_assessments if not assessment.is_review_required
    )

    if enriched_fallback_flag_count >= widget_fallback_flag_count:
        raise ValueError("enriched fallback-entity flag count did not drop")
    if enriched_tender_ref_missing_flag_count >= widget_tender_ref_missing_flag_count:
        raise ValueError("enriched missing tender_ref flag count did not drop")
    if published_missing_flag_count < 1:
        raise ValueError("expected at least one missing published_at flag, got zero")

    first_assessment = enriched_assessments[0]
    if first_assessment.payload.title != enriched_rows[0].title:
        raise ValueError("enriched quality assessment mutated the payload title unexpectedly")

    print(f"verify_abu_dhabi_gpg_enriched_quality_source_name={detail_result.source_name}")
    print(
        "verify_abu_dhabi_gpg_enriched_quality_total_widget_crawled_items="
        f"{crawl_result.total_items}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_total_detail_sampled_items="
        f"{detail_result.sample_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_total_enriched_rows="
        f"{len(enriched_rows)}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_total_assessments="
        f"{len(enriched_assessments)}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_widget_fallback_flag_count="
        f"{widget_fallback_flag_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_enriched_fallback_flag_count="
        f"{enriched_fallback_flag_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_widget_tender_ref_missing_flag_count="
        f"{widget_tender_ref_missing_flag_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_enriched_tender_ref_missing_flag_count="
        f"{enriched_tender_ref_missing_flag_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_published_missing_flag_count="
        f"{published_missing_flag_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_review_required_count="
        f"{review_required_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_higher_confidence_count="
        f"{higher_confidence_count}"
    )
    print(f"verify_abu_dhabi_gpg_enriched_quality_first_title={first_assessment.payload.title}")
    print(
        "verify_abu_dhabi_gpg_enriched_quality_first_tender_ref="
        f"{first_assessment.payload.tender_ref}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_first_score="
        f"{first_assessment.quality_score}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_first_review_required="
        f"{first_assessment.is_review_required}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_quality_first_flags="
        f"{first_assessment.quality_flags}"
    )

    higher_confidence_examples = [
        assessment for assessment in enriched_assessments if not assessment.is_review_required
    ][:3]
    review_required_examples = [
        assessment for assessment in enriched_assessments if assessment.is_review_required
    ][:5]

    print(
        "verify_abu_dhabi_gpg_enriched_quality_higher_confidence_examples_available="
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
    except (AbuDhabiGPGCrawlerError, AbuDhabiGPGDetailCrawlerError) as exc:
        print(
            f"ABU_DHABI_GPG ENRICHED QUALITY VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
