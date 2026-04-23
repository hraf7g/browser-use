from __future__ import annotations

import asyncio
import sys

from src.crawler.sources.abu_dhabi_gpg_crawler import (
    AbuDhabiGPGCrawlerError,
    AbuDhabiGPGCrawlResult,
    run_abu_dhabi_gpg_crawl,
)


def _truncate(value: str | None, limit: int = 180) -> str:
    """Return a compact single-line preview for verification output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _print_summary(result: AbuDhabiGPGCrawlResult) -> None:
    """Print a compact verification summary of the crawl result."""
    print(f"verify_abu_dhabi_gpg_source_name={result.source_name}")
    print(f"verify_abu_dhabi_gpg_listing_url={result.listing_url}")
    print(f"verify_abu_dhabi_gpg_final_url={result.final_url}")
    print(f"verify_abu_dhabi_gpg_page_title={result.page_title}")
    print(f"verify_abu_dhabi_gpg_extracted_at={result.extracted_at.isoformat()}")
    print(f"verify_abu_dhabi_gpg_total_items={result.total_items}")

    if result.total_items > 0:
        first_item = result.items[0]
        print(f"verify_abu_dhabi_gpg_first_item_title={first_item.title_text}")
        print(f"verify_abu_dhabi_gpg_first_item_href={first_item.detail_url}")
        print(
            "verify_abu_dhabi_gpg_first_item_due_date="
            f"{first_item.visible_due_date}"
        )
        print(
            "verify_abu_dhabi_gpg_first_item_category_label="
            f"{first_item.visible_category_label}"
        )
        print(
            "verify_abu_dhabi_gpg_first_item_notice_type="
            f"{first_item.visible_notice_type}"
        )
        print(
            "verify_abu_dhabi_gpg_first_item_short_description="
            f"{_truncate(first_item.visible_short_description)}"
        )
        print(
            "verify_abu_dhabi_gpg_first_item_raw_preview="
            f"{_truncate(first_item.raw_text)}"
        )

    sample_count = min(3, result.total_items)
    for item_index in range(sample_count):
        item = result.items[item_index]
        print(
            f"verify_abu_dhabi_gpg_sample_{item_index}_title="
            f"{_truncate(item.title_text, limit=120)}"
        )
        print(f"verify_abu_dhabi_gpg_sample_{item_index}_href={item.detail_url}")
        print(
            "verify_abu_dhabi_gpg_sample_"
            f"{item_index}_due_date={item.visible_due_date}"
        )
        print(
            "verify_abu_dhabi_gpg_sample_"
            f"{item_index}_category_label={item.visible_category_label}"
        )
        print(
            "verify_abu_dhabi_gpg_sample_"
            f"{item_index}_notice_type={item.visible_notice_type}"
        )


async def _run() -> None:
    """Execute the crawler and validate the raw extraction result."""
    result = await run_abu_dhabi_gpg_crawl()

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
    except AbuDhabiGPGCrawlerError as exc:
        print(f"ABU_DHABI_GPG CRAWLER VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
