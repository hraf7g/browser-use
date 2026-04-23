from __future__ import annotations

import asyncio
import sys

from src.crawler.sources.saudi_etimad_crawler import (
    SaudiEtimadCrawlerError,
    SaudiEtimadCrawlResult,
    run_saudi_etimad_crawl,
)


def _truncate(value: str, limit: int = 180) -> str:
    """Return a compact single-line preview for verification output."""
    value = value.replace("\n", " | ").strip()
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _print_summary(result: SaudiEtimadCrawlResult) -> None:
    """Print a compact verification summary of the crawl result."""
    print(f"verify_saudi_etimad_source_name={result.source_name}")
    print(f"verify_saudi_etimad_listing_url={result.listing_url}")
    print(f"verify_saudi_etimad_final_url={result.final_url}")
    print(f"verify_saudi_etimad_page_title={result.page_title}")
    print(f"verify_saudi_etimad_extracted_at={result.extracted_at.isoformat()}")
    print(f"verify_saudi_etimad_total_items={result.total_items}")

    if result.total_items > 0:
        first_item = result.items[0]
        print(f"verify_saudi_etimad_first_item_title={first_item.title_text}")
        print(f"verify_saudi_etimad_first_item_href={first_item.detail_url}")
        print(
            "verify_saudi_etimad_first_item_reference_fields="
            f"{first_item.reference_fields}"
        )
        print(
            f"verify_saudi_etimad_first_item_date_fields={first_item.date_fields}"
        )
        print(
            "verify_saudi_etimad_first_item_raw_preview="
            f"{_truncate(first_item.raw_text)}"
        )

    sample_count = min(3, result.total_items)
    for item_index in range(sample_count):
        item = result.items[item_index]
        print(
            f"verify_saudi_etimad_sample_{item_index}_title="
            f"{_truncate(item.title_text, limit=120)}"
        )
        print(f"verify_saudi_etimad_sample_{item_index}_href={item.detail_url}")


async def _run() -> None:
    """Execute the crawler and validate the raw extraction result."""
    result = await run_saudi_etimad_crawl()

    if result.total_items < 1:
        raise ValueError("expected at least one extracted item, got zero")

    for item in result.items:
        if not item.title_text.strip():
            raise ValueError(f"item {item.item_index} has empty title_text")
        if not item.detail_url.strip():
            raise ValueError(f"item {item.item_index} has empty href")
        if not item.raw_text.strip():
            raise ValueError(f"item {item.item_index} has empty raw_text")

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except SaudiEtimadCrawlerError as exc:
        print(f"SAUDI_ETIMAD CRAWLER VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
