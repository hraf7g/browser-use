from __future__ import annotations

import asyncio
import sys
from urllib.parse import parse_qsl, urlparse

from src.crawler.sources.oman_tender_board_crawler import (
    OmanTenderBoardCrawlerError,
    OmanTenderBoardCrawlResult,
    run_oman_tender_board_crawl,
)


def _truncate(value: str | None, limit: int = 140) -> str:
    """Return a compact one-line preview for verification output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _print_summary(result: OmanTenderBoardCrawlResult) -> None:
    """Print a compact verification summary of mapped listing fields."""
    print(f"verify_oman_tender_board_mapping_source_name={result.source_name}")
    print(f"verify_oman_tender_board_mapping_listing_url={result.listing_url}")
    print(f"verify_oman_tender_board_mapping_final_url={result.final_url}")
    print(f"verify_oman_tender_board_mapping_page_title={result.page_title}")
    print(f"verify_oman_tender_board_mapping_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"verify_oman_tender_board_mapping_item_{index}_title={_truncate(item.title_text)}")
        print(
            "verify_oman_tender_board_mapping_item_"
            f"{index}_tender_number={_truncate(item.visible_tender_number)}"
        )
        print(
            f"verify_oman_tender_board_mapping_item_{index}_entity="
            f"{_truncate(item.visible_entity)}"
        )
        print(
            "verify_oman_tender_board_mapping_item_"
            f"{index}_procurement_category={_truncate(item.visible_procurement_category)}"
        )
        print(
            "verify_oman_tender_board_mapping_item_"
            f"{index}_tender_type={_truncate(item.visible_tender_type)}"
        )
        print(
            "verify_oman_tender_board_mapping_item_"
            f"{index}_sales_end_date={_truncate(item.visible_sales_end_date)}"
        )
        print(
            "verify_oman_tender_board_mapping_item_"
            f"{index}_bid_closing_date={_truncate(item.visible_bid_closing_date)}"
        )
        print(f"verify_oman_tender_board_mapping_item_{index}_detail_url={item.detail_url}")


def _validate_item(item_index: int, result: OmanTenderBoardCrawlResult) -> None:
    """Validate deterministic mapping expectations for a single item."""
    item = result.items[item_index]

    if not item.title_text.strip():
        raise ValueError(f"item {item.item_index} has empty title_text")
    if not item.detail_url.strip():
        raise ValueError(f"item {item.item_index} has empty detail_url")

    parsed = urlparse(item.detail_url)
    if parsed.scheme != "https" or parsed.netloc != "etendering.tenderboard.gov.om":
        raise ValueError(f"item {item.item_index} detail_url is not on the expected host")
    if parsed.path != "/product/nitParameterView":
        raise ValueError(f"item {item.item_index} detail_url path is unexpected")

    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if query_pairs.get("mode") != "public":
        raise ValueError(f"item {item.item_index} detail_url mode is not public")
    if not query_pairs.get("tenderNo"):
        raise ValueError(f"item {item.item_index} detail_url has no non-empty tenderNo")
    if query_pairs.get("PublicUrl") != "1":
        raise ValueError(f"item {item.item_index} detail_url has no PublicUrl=1")

    raw_text = item.raw_text
    if item.visible_tender_number is not None and item.visible_tender_number not in raw_text:
        raise ValueError(
            f"item {item.item_index} visible_tender_number was not actually found in raw row text"
        )
    if item.visible_entity is not None and item.visible_entity not in raw_text:
        raise ValueError(
            f"item {item.item_index} visible_entity was not actually found in raw row text"
        )
    if (
        item.visible_procurement_category is not None
        and item.visible_procurement_category not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} visible_procurement_category was not found in raw row text"
        )
    if item.visible_tender_type is not None and item.visible_tender_type not in raw_text:
        raise ValueError(
            f"item {item.item_index} visible_tender_type was not found in raw row text"
        )
    if (
        item.visible_sales_end_date is not None
        and f"Sales EndDate:{item.visible_sales_end_date}" not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} visible_sales_end_date did not match visible row text"
        )
    if (
        item.visible_bid_closing_date is not None
        and f"Bid Closing Date:{item.visible_bid_closing_date}" not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} visible_bid_closing_date did not match visible row text"
        )


async def _run() -> None:
    """Execute row-mapping verification against the live Oman Tender Board listing."""
    result = await run_oman_tender_board_crawl()

    if result.total_items < 1:
        raise ValueError("expected at least one mapped item, got zero")

    for item_index in range(min(5, result.total_items)):
        _validate_item(item_index, result)

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except OmanTenderBoardCrawlerError as exc:
        print(
            f"OMAN_TENDER_BOARD ROW MAPPING VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
