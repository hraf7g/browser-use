from __future__ import annotations

import asyncio
import sys

from src.crawler.sources.oman_tender_board_crawler import (
    OmanTenderBoardCrawlerError,
    OmanTenderBoardCrawlResult,
    run_oman_tender_board_crawl,
)


def _truncate(value: str, limit: int = 180) -> str:
    """Return a compact single-line preview for verification output."""
    value = value.replace("\n", " | ").strip()
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _print_summary(result: OmanTenderBoardCrawlResult) -> None:
    """Print a compact verification summary of the crawl result."""
    print(f"verify_oman_tender_board_source_name={result.source_name}")
    print(f"verify_oman_tender_board_listing_url={result.listing_url}")
    print(f"verify_oman_tender_board_final_url={result.final_url}")
    print(f"verify_oman_tender_board_page_title={result.page_title}")
    print(f"verify_oman_tender_board_extracted_at={result.extracted_at.isoformat()}")
    print(f"verify_oman_tender_board_total_items={result.total_items}")

    if result.total_items > 0:
        first_item = result.items[0]
        print(f"verify_oman_tender_board_first_item_title={first_item.title_text}")
        print(f"verify_oman_tender_board_first_item_href={first_item.detail_url}")
        print(
            "verify_oman_tender_board_first_item_tender_number="
            f"{first_item.visible_tender_number}"
        )
        print(
            f"verify_oman_tender_board_first_item_entity={first_item.visible_entity}"
        )
        print(
            "verify_oman_tender_board_first_item_procurement_category="
            f"{first_item.visible_procurement_category}"
        )
        print(
            "verify_oman_tender_board_first_item_tender_type="
            f"{first_item.visible_tender_type}"
        )
        print(
            "verify_oman_tender_board_first_item_sales_end_date="
            f"{first_item.visible_sales_end_date}"
        )
        print(
            "verify_oman_tender_board_first_item_bid_closing_date="
            f"{first_item.visible_bid_closing_date}"
        )
        print(
            "verify_oman_tender_board_first_item_raw_preview="
            f"{_truncate(first_item.raw_text)}"
        )

    sample_count = min(3, result.total_items)
    for item_index in range(sample_count):
        item = result.items[item_index]
        print(
            f"verify_oman_tender_board_sample_{item_index}_title="
            f"{_truncate(item.title_text, limit=120)}"
        )
        print(f"verify_oman_tender_board_sample_{item_index}_href={item.detail_url}")
        print(
            "verify_oman_tender_board_sample_"
            f"{item_index}_tender_number={item.visible_tender_number}"
        )
        print(
            "verify_oman_tender_board_sample_"
            f"{item_index}_entity={item.visible_entity}"
        )
        print(
            "verify_oman_tender_board_sample_"
            f"{item_index}_procurement_category={item.visible_procurement_category}"
        )
        print(
            "verify_oman_tender_board_sample_"
            f"{item_index}_tender_type={item.visible_tender_type}"
        )
        print(
            "verify_oman_tender_board_sample_"
            f"{item_index}_sales_end_date={item.visible_sales_end_date}"
        )
        print(
            "verify_oman_tender_board_sample_"
            f"{item_index}_bid_closing_date={item.visible_bid_closing_date}"
        )


async def _run() -> None:
    """Execute the crawler and validate the raw extraction result."""
    result = await run_oman_tender_board_crawl()

    if result.total_items < 1:
        raise ValueError("expected at least one extracted item, got zero")

    for item in result.items:
        if not item.title_text.strip():
            raise ValueError(f"item {item.item_index} has empty title_text")
        if not item.detail_url.strip():
            raise ValueError(f"item {item.item_index} has empty detail_url")
        if not item.raw_text.strip():
            raise ValueError(f"item {item.item_index} has empty raw_text")
        if item.visible_tender_number is None:
            raise ValueError(f"item {item.item_index} is missing visible_tender_number")

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except OmanTenderBoardCrawlerError as exc:
        print(f"OMAN_TENDER_BOARD CRAWLER VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
