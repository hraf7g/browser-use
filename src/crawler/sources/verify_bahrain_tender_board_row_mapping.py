from __future__ import annotations

import asyncio
import sys
from urllib.parse import parse_qsl, urlparse

from src.crawler.sources.bahrain_tender_board_crawler import (
    BahrainTenderBoardCrawlerError,
    BahrainTenderBoardCrawlResult,
    run_bahrain_tender_board_crawl,
)


def _truncate(value: str | None, limit: int = 140) -> str:
    """Return a compact one-line preview for verification output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _validate_item(item_index: int, result: BahrainTenderBoardCrawlResult) -> None:
    """Validate deterministic row mapping expectations for a single item."""
    item = result.items[item_index]

    if not item.title_text.strip():
        raise ValueError(f"item {item.item_index} has empty title_text")
    if not item.detail_url.strip():
        raise ValueError(f"item {item.item_index} has empty detail_url")

    parsed = urlparse(item.detail_url)
    if parsed.scheme != "https" or parsed.netloc != "etendering.tenderboard.gov.bh":
        raise ValueError(f"item {item.item_index} detail_url is not on the expected host")
    if parsed.path != "/Tenders/nitParameterView":
        raise ValueError(f"item {item.item_index} detail_url path is unexpected")

    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if query_pairs.get("mode") != "public":
        raise ValueError(f"item {item.item_index} detail_url mode is not public")
    if query_pairs.get("PublicUrl") != "1":
        raise ValueError(f"item {item.item_index} detail_url is missing PublicUrl=1")
    if not query_pairs.get("tenderNo"):
        raise ValueError(f"item {item.item_index} detail_url has no non-empty tenderNo")

    raw_lines = item.raw_text.splitlines()
    if len(raw_lines) < 1:
        raise ValueError(f"item {item.item_index} raw_text has no visible lines")

    first_line = raw_lines[0]
    if item.visible_tender_number is not None and item.visible_tender_number not in first_line:
        raise ValueError(
            f"item {item.item_index} visible_tender_number was not found in the visible first line"
        )

    if item.visible_pa_reference is not None and item.visible_pa_reference not in first_line:
        raise ValueError(
            f"item {item.item_index} visible_pa_reference was not found in the visible first line"
        )

    if len(raw_lines) >= 2:
        expected_title_line = raw_lines[1].strip("() ").strip()
        if expected_title_line and item.title_text not in expected_title_line:
            raise ValueError(
                f"item {item.item_index} title_text was not found in the visible dashboard title line"
            )

    if item.visible_entity is not None and item.visible_entity not in item.raw_text:
        raise ValueError(
            f"item {item.item_index} visible_entity was not found in visible row text"
        )

    if item.visible_time_left is not None and item.visible_time_left not in item.raw_text:
        raise ValueError(
            f"item {item.item_index} visible_time_left was not found in visible row text"
        )


def _print_summary(result: BahrainTenderBoardCrawlResult) -> None:
    """Print a compact verification summary of mapped dashboard fields."""
    print(f"verify_bahrain_tender_board_mapping_source_name={result.source_name}")
    print(f"verify_bahrain_tender_board_mapping_listing_url={result.listing_url}")
    print(f"verify_bahrain_tender_board_mapping_final_url={result.final_url}")
    print(f"verify_bahrain_tender_board_mapping_page_title={result.page_title}")
    print(f"verify_bahrain_tender_board_mapping_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(
            f"verify_bahrain_tender_board_mapping_item_{index}_title="
            f"{_truncate(item.title_text)}"
        )
        print(
            "verify_bahrain_tender_board_mapping_item_"
            f"{index}_tender_number={_truncate(item.visible_tender_number)}"
        )
        print(
            "verify_bahrain_tender_board_mapping_item_"
            f"{index}_pa_reference={_truncate(item.visible_pa_reference)}"
        )
        print(
            "verify_bahrain_tender_board_mapping_item_"
            f"{index}_entity={_truncate(item.visible_entity)}"
        )
        print(
            "verify_bahrain_tender_board_mapping_item_"
            f"{index}_time_left={_truncate(item.visible_time_left)}"
        )
        print(
            f"verify_bahrain_tender_board_mapping_item_{index}_detail_url={item.detail_url}"
        )


async def _run() -> None:
    """Execute row-mapping verification against the live Bahrain public dashboard."""
    result = await run_bahrain_tender_board_crawl()

    if result.total_items < 1:
        raise ValueError("expected at least one mapped item, got zero")

    for item_index in range(min(5, result.total_items)):
        _validate_item(item_index, result)

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except BahrainTenderBoardCrawlerError as exc:
        print(
            f"BAHRAIN_TENDER_BOARD ROW MAPPING VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
