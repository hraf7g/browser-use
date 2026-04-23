from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from src.crawler.sources.saudi_misa_crawler import (
    SaudiMisaCrawlerError,
    run_saudi_misa_crawl,
)
from src.crawler.sources.saudi_misa_normalizer import normalize_saudi_misa_items

SAUDI_MISA_VERIFICATION_SOURCE_ID = UUID("77777777-7777-7777-7777-777777777777")


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
    Execute live crawl plus Saudi MISA normalization verification.

    This script verifies:
    - at least one raw table row exists
    - normalization produces at least one TenderIngestionInput
    - required fields are populated deterministically
    - tender_ref is preserved from visible reference number
    - published_at is parsed from the visible offering date when present
    - closing_date is parsed from the visible bid deadline when present
    - optional fields remain optional instead of being guessed
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

    for raw_item, normalized_row in zip(crawl_result.items, normalized_rows, strict=False):
        if not normalized_row.title.strip():
            raise ValueError(f"normalized item {raw_item.item_index} has empty title")
        if not normalized_row.dedupe_key.strip():
            raise ValueError(f"normalized item {raw_item.item_index} has empty dedupe_key")
        if not normalized_row.source_url.strip():
            raise ValueError(f"normalized item {raw_item.item_index} has empty source_url")

        if normalized_row.source_url != raw_item.detail_url:
            raise ValueError(
                f"normalized item {raw_item.item_index} did not preserve the visible detail URL"
            )

        if normalized_row.tender_ref != raw_item.visible_reference_number:
            raise ValueError(
                f"normalized item {raw_item.item_index} did not preserve visible reference_number"
            )

        if normalized_row.category is not None:
            raise ValueError(
                f"normalized item {raw_item.item_index} invented category '{normalized_row.category}'"
            )

        if normalized_row.opening_date is not None:
            raise ValueError(
                f"normalized item {raw_item.item_index} invented opening_date '{normalized_row.opening_date}'"
            )

        if (
            raw_item.visible_offering_date is not None
            and normalized_row.published_at is None
        ):
            raise ValueError(
                f"normalized item {raw_item.item_index} did not parse published_at from visible offering date"
            )
        if raw_item.visible_bid_deadline is not None and normalized_row.closing_date is None:
            raise ValueError(
                f"normalized item {raw_item.item_index} left closing_date empty despite visible bid deadline"
            )

    first_row = normalized_rows[0]
    missing_closing_date_count = sum(
        1 for row in normalized_rows if row.closing_date is None
    )
    issuing_entity_misa_count = sum(
        1 for row in normalized_rows if row.issuing_entity == "MISA"
    )

    print(f"verify_saudi_misa_normalizer_source_name={crawl_result.source_name}")
    print(f"verify_saudi_misa_normalizer_listing_url={crawl_result.listing_url}")
    print(f"verify_saudi_misa_normalizer_total_crawled_items={crawl_result.total_items}")
    print(
        "verify_saudi_misa_normalizer_total_normalized_rows="
        f"{len(normalized_rows)}"
    )
    print(f"verify_saudi_misa_normalizer_first_title={first_row.title}")
    print(
        "verify_saudi_misa_normalizer_first_issuing_entity="
        f"{first_row.issuing_entity}"
    )
    print(
        "verify_saudi_misa_normalizer_first_published_at="
        f"{first_row.published_at.isoformat() if first_row.published_at else None}"
    )
    print(
        "verify_saudi_misa_normalizer_first_closing_date="
        f"{first_row.closing_date.isoformat() if first_row.closing_date else None}"
    )
    print(
        "verify_saudi_misa_normalizer_first_tender_ref="
        f"{first_row.tender_ref}"
    )
    print(f"verify_saudi_misa_normalizer_first_category={first_row.category}")
    print(
        "verify_saudi_misa_normalizer_first_dedupe_key="
        f"{first_row.dedupe_key}"
    )
    print(
        "verify_saudi_misa_normalizer_first_source_url="
        f"{first_row.source_url}"
    )
    print(
        "verify_saudi_misa_normalizer_missing_closing_date_count="
        f"{missing_closing_date_count}"
    )
    print(
        "verify_saudi_misa_normalizer_issuing_entity_misa_used="
        f"{issuing_entity_misa_count}"
    )

    sample_count = min(5, len(normalized_rows))
    for index in range(sample_count):
        row = normalized_rows[index]
        print(
            f"verify_saudi_misa_normalizer_sample_{index}_title={_truncate(row.title)}"
        )
        print(
            "verify_saudi_misa_normalizer_sample_"
            f"{index}_issuing_entity={_truncate(row.issuing_entity)}"
        )
        print(
            "verify_saudi_misa_normalizer_sample_"
            f"{index}_published_at={row.published_at.isoformat() if row.published_at else None}"
        )
        print(
            "verify_saudi_misa_normalizer_sample_"
            f"{index}_closing_date={row.closing_date.isoformat() if row.closing_date else None}"
        )
        print(
            f"verify_saudi_misa_normalizer_sample_{index}_tender_ref={row.tender_ref}"
        )
        print(f"verify_saudi_misa_normalizer_sample_{index}_category={row.category}")
        print(
            f"verify_saudi_misa_normalizer_sample_{index}_source_url={row.source_url}"
        )


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except SaudiMisaCrawlerError as exc:
        print(f"SAUDI_MISA NORMALIZER VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
