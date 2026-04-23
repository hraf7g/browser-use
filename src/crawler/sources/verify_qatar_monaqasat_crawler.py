from __future__ import annotations

import asyncio
import sys

from src.crawler.sources.qatar_monaqasat_crawler import (
    QatarMonaqasatCrawlerError,
    QatarMonaqasatCrawlResult,
    run_qatar_monaqasat_crawl,
)


def _truncate(value: str, limit: int = 180) -> str:
    """Return a compact single-line preview for verification output."""
    value = value.replace("\n", " | ").strip()
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _print_summary(result: QatarMonaqasatCrawlResult) -> None:
    """Print a compact verification summary of the crawl result."""
    print(f"verify_qatar_monaqasat_source_name={result.source_name}")
    print(f"verify_qatar_monaqasat_listing_url={result.listing_url}")
    print(f"verify_qatar_monaqasat_final_url={result.final_url}")
    print(f"verify_qatar_monaqasat_page_title={result.page_title}")
    print(f"verify_qatar_monaqasat_extracted_at={result.extracted_at.isoformat()}")
    print(f"verify_qatar_monaqasat_total_items={result.total_items}")

    if result.total_items > 0:
        first_item = result.items[0]
        print(f"verify_qatar_monaqasat_first_item_title={first_item.title_text}")
        print(f"verify_qatar_monaqasat_first_item_href={first_item.detail_url}")
        print(f"verify_qatar_monaqasat_first_item_reference={first_item.visible_reference}")
        print(f"verify_qatar_monaqasat_first_item_publish_date={first_item.visible_publish_date}")
        print(f"verify_qatar_monaqasat_first_item_ministry={first_item.visible_ministry}")
        print(f"verify_qatar_monaqasat_first_item_type={first_item.visible_tender_type}")
        print(
            "verify_qatar_monaqasat_first_item_raw_preview="
            f"{_truncate(first_item.raw_text)}"
        )

    sample_count = min(3, result.total_items)
    for item_index in range(sample_count):
        item = result.items[item_index]
        print(
            f"verify_qatar_monaqasat_sample_{item_index}_title="
            f"{_truncate(item.title_text, limit=120)}"
        )
        print(f"verify_qatar_monaqasat_sample_{item_index}_href={item.detail_url}")
        print(
            f"verify_qatar_monaqasat_sample_{item_index}_reference={item.visible_reference}"
        )
        print(
            f"verify_qatar_monaqasat_sample_{item_index}_publish_date={item.visible_publish_date}"
        )
        print(
            f"verify_qatar_monaqasat_sample_{item_index}_ministry={item.visible_ministry}"
        )
        print(
            f"verify_qatar_monaqasat_sample_{item_index}_type={item.visible_tender_type}"
        )


async def _run() -> None:
    """Execute the crawler and validate the raw extraction result."""
    result = await run_qatar_monaqasat_crawl()

    if result.total_items < 1:
        raise ValueError("expected at least one extracted item, got zero")

    for item in result.items:
        if not item.title_text.strip():
            raise ValueError(f"item {item.item_index} has empty title_text")
        if not item.detail_url.strip():
            raise ValueError(f"item {item.item_index} has empty detail_url")
        if not item.raw_text.strip():
            raise ValueError(f"item {item.item_index} has empty raw_text")

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except QatarMonaqasatCrawlerError as exc:
        print(f"QATAR_MONAQASAT CRAWLER VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
