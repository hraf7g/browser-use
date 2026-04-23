from __future__ import annotations

import asyncio
import sys
from urllib.parse import parse_qsl, urlparse

from src.crawler.sources.saudi_misa_crawler import (
    SaudiMisaCrawlerError,
    SaudiMisaCrawlResult,
    run_saudi_misa_crawl,
)


def _truncate(value: str | None, limit: int = 140) -> str:
    """Return a compact one-line preview for verification output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _print_summary(result: SaudiMisaCrawlResult) -> None:
    """Print a compact verification summary of mapped table fields."""
    print(f"verify_saudi_misa_mapping_source_name={result.source_name}")
    print(f"verify_saudi_misa_mapping_listing_url={result.listing_url}")
    print(f"verify_saudi_misa_mapping_final_url={result.final_url}")
    print(f"verify_saudi_misa_mapping_page_title={result.page_title}")
    print(f"verify_saudi_misa_mapping_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"verify_saudi_misa_mapping_item_{index}_title={_truncate(item.title_text)}")
        print(
            "verify_saudi_misa_mapping_item_"
            f"{index}_reference_number={_truncate(item.visible_reference_number)}"
        )
        print(
            "verify_saudi_misa_mapping_item_"
            f"{index}_offering_date={_truncate(item.visible_offering_date)}"
        )
        print(
            "verify_saudi_misa_mapping_item_"
            f"{index}_inquiry_deadline={_truncate(item.visible_inquiry_deadline)}"
        )
        print(
            "verify_saudi_misa_mapping_item_"
            f"{index}_bid_deadline={_truncate(item.visible_bid_deadline)}"
        )
        print(
            "verify_saudi_misa_mapping_item_"
            f"{index}_status_link_text={_truncate(item.visible_status_link_text)}"
        )
        print(f"verify_saudi_misa_mapping_item_{index}_detail_url={item.detail_url}")


def _validate_item(item_index: int, result: SaudiMisaCrawlResult) -> None:
    """Validate deterministic mapping expectations for a single item."""
    item = result.items[item_index]

    if not item.title_text.strip():
        raise ValueError(f"item {item.item_index} has empty title_text")
    if not item.detail_url.strip():
        raise ValueError(f"item {item.item_index} has empty detail_url")

    parsed = urlparse(item.detail_url)
    if parsed.scheme != "https" or parsed.netloc != "tenders.etimad.sa":
        raise ValueError(f"item {item.item_index} detail_url is not on the expected host")
    if parsed.path != "/Tender/DetailsForVisitor":
        raise ValueError(f"item {item.item_index} detail_url path is unexpected")

    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if not query_pairs.get("STenderId"):
        raise ValueError(f"item {item.item_index} detail_url has no non-empty STenderId")

    raw_text = item.raw_text
    if (
        item.visible_reference_number is not None
        and item.visible_reference_number not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} visible_reference_number was not found in raw row text"
        )
    if (
        item.visible_offering_date is not None
        and item.visible_offering_date not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} offering_date was not found in raw row text"
        )
    if (
        item.visible_inquiry_deadline is not None
        and item.visible_inquiry_deadline not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} inquiry_deadline was not found in raw row text"
        )
    if (
        item.visible_bid_deadline is not None
        and item.visible_bid_deadline not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} bid_deadline was not found in raw row text"
        )
    if (
        item.visible_status_link_text is not None
        and item.visible_status_link_text not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} status_link_text was not found in raw row text"
        )


async def _run() -> None:
    """Execute row-mapping verification against the live Saudi MISA table."""
    result = await run_saudi_misa_crawl()

    if result.total_items < 1:
        raise ValueError("expected at least one mapped item, got zero")

    for item_index in range(min(5, result.total_items)):
        _validate_item(item_index, result)

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except SaudiMisaCrawlerError as exc:
        print(f"SAUDI_MISA ROW MAPPING VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
