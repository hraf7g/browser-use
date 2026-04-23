from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from src.crawler.sources.oman_tender_board_crawler import (
    OmanTenderBoardCrawlerError,
    run_oman_tender_board_crawl,
)
from src.crawler.sources.oman_tender_board_normalizer import (
    normalize_oman_tender_board_items,
)

OMAN_TENDER_BOARD_VERIFICATION_SOURCE_ID = UUID("77777777-7777-7777-7777-777777777777")


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
    Execute live crawl plus Oman Tender Board normalization verification.

    This script verifies:
    - at least one raw listing item exists
    - normalization produces at least one TenderIngestionInput
    - required fields are populated deterministically
    - tender_ref is preserved from visible tender number
    - category is preserved from visible procurement category
    - closing_date is parsed from visible bid-closing date
    - optional fields remain optional instead of being guessed
    """
    crawl_result = await run_oman_tender_board_crawl()
    if crawl_result.total_items < 1:
        raise ValueError("expected at least one crawled item, got zero")

    normalized_rows = normalize_oman_tender_board_items(
        source_id=OMAN_TENDER_BOARD_VERIFICATION_SOURCE_ID,
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

        if normalized_row.tender_ref != raw_item.visible_tender_number:
            raise ValueError(
                f"normalized item {raw_item.item_index} changed visible tender_ref"
            )

        if normalized_row.issuing_entity != raw_item.visible_entity:
            raise ValueError(
                f"normalized item {raw_item.item_index} changed visible issuing_entity"
            )

        if normalized_row.category != raw_item.visible_procurement_category:
            raise ValueError(
                f"normalized item {raw_item.item_index} changed visible procurement category"
            )

        if normalized_row.opening_date is not None:
            raise ValueError(
                f"normalized item {raw_item.item_index} invented opening_date '{normalized_row.opening_date}'"
            )

        if normalized_row.published_at is not None:
            raise ValueError(
                f"normalized item {raw_item.item_index} invented published_at '{normalized_row.published_at}'"
            )

    first_row = normalized_rows[0]
    print(f"verify_oman_tender_board_normalizer_source_name={crawl_result.source_name}")
    print(f"verify_oman_tender_board_normalizer_listing_url={crawl_result.listing_url}")
    print(f"verify_oman_tender_board_normalizer_total_crawled_items={crawl_result.total_items}")
    print(f"verify_oman_tender_board_normalizer_total_normalized_rows={len(normalized_rows)}")
    print(f"verify_oman_tender_board_normalizer_first_title={first_row.title}")
    print(
        "verify_oman_tender_board_normalizer_first_issuing_entity="
        f"{first_row.issuing_entity}"
    )
    print(
        "verify_oman_tender_board_normalizer_first_published_at="
        f"{first_row.published_at.isoformat() if first_row.published_at else None}"
    )
    print(
        "verify_oman_tender_board_normalizer_first_closing_date="
        f"{first_row.closing_date.isoformat()}"
    )
    print(
        "verify_oman_tender_board_normalizer_first_tender_ref="
        f"{first_row.tender_ref}"
    )
    print(
        "verify_oman_tender_board_normalizer_first_category="
        f"{first_row.category}"
    )
    print(
        "verify_oman_tender_board_normalizer_first_dedupe_key="
        f"{first_row.dedupe_key}"
    )
    print(
        "verify_oman_tender_board_normalizer_first_source_url="
        f"{first_row.source_url}"
    )

    sample_count = min(5, len(normalized_rows))
    for index in range(sample_count):
        row = normalized_rows[index]
        print(
            f"verify_oman_tender_board_normalizer_sample_{index}_title={_truncate(row.title)}"
        )
        print(
            "verify_oman_tender_board_normalizer_sample_"
            f"{index}_issuing_entity={_truncate(row.issuing_entity)}"
        )
        print(
            "verify_oman_tender_board_normalizer_sample_"
            f"{index}_published_at={row.published_at.isoformat() if row.published_at else None}"
        )
        print(
            "verify_oman_tender_board_normalizer_sample_"
            f"{index}_closing_date={row.closing_date.isoformat()}"
        )
        print(
            f"verify_oman_tender_board_normalizer_sample_{index}_tender_ref={row.tender_ref}"
        )
        print(
            f"verify_oman_tender_board_normalizer_sample_{index}_category={row.category}"
        )
        print(
            f"verify_oman_tender_board_normalizer_sample_{index}_source_url={row.source_url}"
        )


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except OmanTenderBoardCrawlerError as exc:
        print(
            f"OMAN_TENDER_BOARD NORMALIZER VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
