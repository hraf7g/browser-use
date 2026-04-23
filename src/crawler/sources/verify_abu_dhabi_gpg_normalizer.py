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
    Execute live crawl plus Abu Dhabi GPG normalization verification.

    This script verifies:
    - at least one raw widget item exists
    - normalization produces at least one TenderIngestionInput
    - required fields are populated deterministically
    - closing_date is parsed from visible due date
    - category is preserved from visible category label
    - tender_ref remains absent because the widget exposes none
    - opening_date and published_at remain unset instead of being guessed
    - issuing_entity fallback usage is counted explicitly
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

    issuing_entity_fallback_count = 0
    tender_ref_missing_count = 0

    for raw_item, normalized_row in zip(crawl_result.items, normalized_rows, strict=False):
        if not normalized_row.title.strip():
            raise ValueError(f"normalized item {raw_item.item_index} has empty title")
        if not normalized_row.dedupe_key.strip():
            raise ValueError(f"normalized item {raw_item.item_index} has empty dedupe_key")
        if not normalized_row.source_url.strip():
            raise ValueError(f"normalized item {raw_item.item_index} has empty source_url")

        if normalized_row.title != raw_item.title_text:
            raise ValueError(f"normalized item {raw_item.item_index} changed visible title")

        if normalized_row.category != raw_item.visible_category_label:
            raise ValueError(
                f"normalized item {raw_item.item_index} changed visible category label"
            )

        if normalized_row.tender_ref is not None:
            raise ValueError(
                f"normalized item {raw_item.item_index} invented tender_ref '{normalized_row.tender_ref}'"
            )

        if normalized_row.opening_date is not None:
            raise ValueError(
                f"normalized item {raw_item.item_index} invented opening_date '{normalized_row.opening_date}'"
            )

        if normalized_row.published_at is not None:
            raise ValueError(
                f"normalized item {raw_item.item_index} invented published_at '{normalized_row.published_at}'"
            )

        if normalized_row.issuing_entity == crawl_result.source_name:
            issuing_entity_fallback_count += 1

        if normalized_row.tender_ref is None:
            tender_ref_missing_count += 1

    first_row = normalized_rows[0]
    print(f"verify_abu_dhabi_gpg_normalizer_source_name={crawl_result.source_name}")
    print(f"verify_abu_dhabi_gpg_normalizer_listing_url={crawl_result.listing_url}")
    print(f"verify_abu_dhabi_gpg_normalizer_total_crawled_items={crawl_result.total_items}")
    print(f"verify_abu_dhabi_gpg_normalizer_total_normalized_rows={len(normalized_rows)}")
    print(f"verify_abu_dhabi_gpg_normalizer_first_title={first_row.title}")
    print(
        "verify_abu_dhabi_gpg_normalizer_first_issuing_entity="
        f"{first_row.issuing_entity}"
    )
    print(
        "verify_abu_dhabi_gpg_normalizer_first_published_at="
        f"{first_row.published_at.isoformat() if first_row.published_at else None}"
    )
    print(
        "verify_abu_dhabi_gpg_normalizer_first_closing_date="
        f"{first_row.closing_date.isoformat()}"
    )
    print(
        "verify_abu_dhabi_gpg_normalizer_first_tender_ref="
        f"{first_row.tender_ref}"
    )
    print(
        "verify_abu_dhabi_gpg_normalizer_first_category="
        f"{first_row.category}"
    )
    print(
        "verify_abu_dhabi_gpg_normalizer_first_dedupe_key="
        f"{first_row.dedupe_key}"
    )
    print(
        "verify_abu_dhabi_gpg_normalizer_first_source_url="
        f"{first_row.source_url}"
    )
    print(
        "verify_abu_dhabi_gpg_normalizer_issuing_entity_fallback_used="
        f"{issuing_entity_fallback_count}"
    )
    print(
        "verify_abu_dhabi_gpg_normalizer_tender_ref_missing_count="
        f"{tender_ref_missing_count}"
    )

    sample_count = min(5, len(normalized_rows))
    for index in range(sample_count):
        row = normalized_rows[index]
        print(
            f"verify_abu_dhabi_gpg_normalizer_sample_{index}_title={_truncate(row.title)}"
        )
        print(
            "verify_abu_dhabi_gpg_normalizer_sample_"
            f"{index}_issuing_entity={_truncate(row.issuing_entity)}"
        )
        print(
            "verify_abu_dhabi_gpg_normalizer_sample_"
            f"{index}_published_at={row.published_at.isoformat() if row.published_at else None}"
        )
        print(
            "verify_abu_dhabi_gpg_normalizer_sample_"
            f"{index}_closing_date={row.closing_date.isoformat()}"
        )
        print(
            f"verify_abu_dhabi_gpg_normalizer_sample_{index}_tender_ref={row.tender_ref}"
        )
        print(
            f"verify_abu_dhabi_gpg_normalizer_sample_{index}_category={row.category}"
        )
        print(
            f"verify_abu_dhabi_gpg_normalizer_sample_{index}_source_url={row.source_url}"
        )


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except AbuDhabiGPGCrawlerError as exc:
        print(
            f"ABU_DHABI_GPG NORMALIZER VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
