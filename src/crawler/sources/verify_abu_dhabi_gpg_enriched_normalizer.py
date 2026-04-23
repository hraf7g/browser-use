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
from src.crawler.sources.abu_dhabi_gpg_normalizer import (
    normalize_abu_dhabi_gpg_items,
)

ABU_DHABI_GPG_VERIFICATION_SOURCE_ID = UUID("88888888-8888-8888-8888-888888888888")


def _truncate(value: str | None, limit: int = 140) -> str:
    """Return a compact one-line preview for verification output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


async def _run() -> None:
    """
    Execute live detail crawl plus Abu Dhabi GPG enriched-normalization verification.

    This script verifies:
    - at least one normalized row exists
    - detail enrichment is actually being used
    - issuing_entity fallback usage drops versus widget-only normalization
    - tender_ref missing count drops versus widget-only normalization
    - closing_date is parsed from detail pages
    - opening_date is populated when visible
    - published_at remains None unless visibly present
    """
    crawl_result = await run_abu_dhabi_gpg_crawl()
    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled widget item, got zero")

    detail_result = await run_abu_dhabi_gpg_detail_crawl()
    if detail_result.sample_count < 1:
        raise ValueError("expected at least one sampled detail item, got zero")

    widget_only_rows = normalize_abu_dhabi_gpg_items(
        source_id=ABU_DHABI_GPG_VERIFICATION_SOURCE_ID,
        items=crawl_result.items[: detail_result.sample_count],
    )
    enriched_rows = normalize_abu_dhabi_gpg_enriched_items(
        source_id=ABU_DHABI_GPG_VERIFICATION_SOURCE_ID,
        items=detail_result.items,
    )

    if not enriched_rows:
        raise ValueError("expected at least one enriched normalized row, got zero")
    if len(enriched_rows) != detail_result.sample_count:
        raise ValueError("enriched normalized row count does not match sampled detail count")

    widget_fallback_count = sum(
        1 for row in widget_only_rows if row.issuing_entity == detail_result.source_name
    )
    enriched_fallback_count = sum(
        1 for row in enriched_rows if row.issuing_entity == detail_result.source_name
    )
    widget_tender_ref_missing_count = sum(1 for row in widget_only_rows if row.tender_ref is None)
    enriched_tender_ref_missing_count = sum(
        1 for row in enriched_rows if row.tender_ref is None
    )
    opening_date_populated_count = sum(1 for row in enriched_rows if row.opening_date is not None)

    if enriched_fallback_count >= widget_fallback_count:
        raise ValueError("issuing_entity fallback usage did not drop after enrichment")
    if enriched_tender_ref_missing_count >= widget_tender_ref_missing_count:
        raise ValueError("tender_ref missing count did not drop after enrichment")
    if opening_date_populated_count < 1:
        raise ValueError("expected at least one enriched opening_date, got zero")

    enrichment_observed = False
    for detail_item, widget_row, enriched_row in zip(
        detail_result.items,
        widget_only_rows,
        enriched_rows,
        strict=False,
    ):
        if not enriched_row.title.strip():
            raise ValueError(f"enriched item {detail_item.item_index} has empty title")
        if not enriched_row.dedupe_key.strip():
            raise ValueError(f"enriched item {detail_item.item_index} has empty dedupe_key")
        if not enriched_row.source_url.strip():
            raise ValueError(f"enriched item {detail_item.item_index} has empty source_url")

        if enriched_row.source_url != detail_item.detail_url:
            raise ValueError(
                f"enriched item {detail_item.item_index} did not preserve detail_url as source_url"
            )

        expected_title = detail_item.detail_title or detail_item.widget_title_text
        if enriched_row.title != expected_title:
            raise ValueError(
                f"enriched item {detail_item.item_index} did not prefer the strongest title"
            )

        expected_entity = detail_item.detail_issuing_entity or detail_result.source_name
        if enriched_row.issuing_entity != expected_entity:
            raise ValueError(
                f"enriched item {detail_item.item_index} did not prefer the strongest issuing_entity"
            )

        if enriched_row.tender_ref != detail_item.detail_tender_ref:
            raise ValueError(
                f"enriched item {detail_item.item_index} did not preserve detail_tender_ref"
            )

        if detail_item.detail_opening_date_raw is not None and enriched_row.opening_date is None:
            raise ValueError(
                f"enriched item {detail_item.item_index} did not populate opening_date"
            )

        if enriched_row.published_at is not None:
            raise ValueError(
                f"enriched item {detail_item.item_index} invented published_at '{enriched_row.published_at}'"
            )

        if (
            enriched_row.title != widget_row.title
            or enriched_row.issuing_entity != widget_row.issuing_entity
            or enriched_row.tender_ref != widget_row.tender_ref
            or enriched_row.opening_date != widget_row.opening_date
            or enriched_row.category != widget_row.category
        ):
            enrichment_observed = True

    if not enrichment_observed:
        raise ValueError("no enriched row actually differed from widget-only normalization")

    first_row = enriched_rows[0]
    print(f"verify_abu_dhabi_gpg_enriched_normalizer_source_name={detail_result.source_name}")
    print(f"verify_abu_dhabi_gpg_enriched_normalizer_listing_url={detail_result.listing_url}")
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_total_widget_crawled_items="
        f"{crawl_result.total_items}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_total_detail_sampled_items="
        f"{detail_result.sample_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_total_enriched_rows="
        f"{len(enriched_rows)}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_widget_fallback_count="
        f"{widget_fallback_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_enriched_fallback_count="
        f"{enriched_fallback_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_widget_tender_ref_missing_count="
        f"{widget_tender_ref_missing_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_enriched_tender_ref_missing_count="
        f"{enriched_tender_ref_missing_count}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_opening_date_populated_count="
        f"{opening_date_populated_count}"
    )
    print(f"verify_abu_dhabi_gpg_enriched_normalizer_first_title={first_row.title}")
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_first_issuing_entity="
        f"{first_row.issuing_entity}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_first_published_at="
        f"{first_row.published_at.isoformat() if first_row.published_at else None}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_first_opening_date="
        f"{first_row.opening_date.isoformat() if first_row.opening_date else None}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_first_closing_date="
        f"{first_row.closing_date.isoformat()}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_first_tender_ref="
        f"{first_row.tender_ref}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_first_category="
        f"{first_row.category}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_first_dedupe_key="
        f"{first_row.dedupe_key}"
    )
    print(
        "verify_abu_dhabi_gpg_enriched_normalizer_first_source_url="
        f"{first_row.source_url}"
    )

    sample_count = min(5, len(enriched_rows))
    for index in range(sample_count):
        row = enriched_rows[index]
        widget_row = widget_only_rows[index]
        print(
            f"verify_abu_dhabi_gpg_enriched_normalizer_sample_{index}_title={_truncate(row.title)}"
        )
        print(
            "verify_abu_dhabi_gpg_enriched_normalizer_sample_"
            f"{index}_issuing_entity={_truncate(row.issuing_entity)}"
        )
        print(
            "verify_abu_dhabi_gpg_enriched_normalizer_sample_"
            f"{index}_published_at={row.published_at.isoformat() if row.published_at else None}"
        )
        print(
            "verify_abu_dhabi_gpg_enriched_normalizer_sample_"
            f"{index}_opening_date={row.opening_date.isoformat() if row.opening_date else None}"
        )
        print(
            "verify_abu_dhabi_gpg_enriched_normalizer_sample_"
            f"{index}_closing_date={row.closing_date.isoformat()}"
        )
        print(
            f"verify_abu_dhabi_gpg_enriched_normalizer_sample_{index}_tender_ref={row.tender_ref}"
        )
        print(
            f"verify_abu_dhabi_gpg_enriched_normalizer_sample_{index}_category={row.category}"
        )
        print(
            "verify_abu_dhabi_gpg_enriched_normalizer_sample_"
            f"{index}_source_url={row.source_url}"
        )
        print(
            "verify_abu_dhabi_gpg_enriched_normalizer_sample_"
            f"{index}_widget_only_issuing_entity={_truncate(widget_row.issuing_entity)}"
        )
        print(
            "verify_abu_dhabi_gpg_enriched_normalizer_sample_"
            f"{index}_widget_only_tender_ref={widget_row.tender_ref}"
        )


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except (AbuDhabiGPGCrawlerError, AbuDhabiGPGDetailCrawlerError) as exc:
        print(
            f"ABU_DHABI_GPG ENRICHED NORMALIZER VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
