from __future__ import annotations

import asyncio
import sys
from urllib.parse import parse_qsl, urlparse

from src.crawler.sources.abu_dhabi_gpg_crawler import (
    AbuDhabiGPGCrawlerError,
    AbuDhabiGPGCrawlResult,
    run_abu_dhabi_gpg_crawl,
)


def _truncate(value: str | None, limit: int = 140) -> str:
    """Return a compact one-line preview for verification output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _print_summary(result: AbuDhabiGPGCrawlResult) -> None:
    """Print a compact verification summary of mapped widget fields."""
    print(f"verify_abu_dhabi_gpg_mapping_source_name={result.source_name}")
    print(f"verify_abu_dhabi_gpg_mapping_listing_url={result.listing_url}")
    print(f"verify_abu_dhabi_gpg_mapping_final_url={result.final_url}")
    print(f"verify_abu_dhabi_gpg_mapping_page_title={result.page_title}")
    print(f"verify_abu_dhabi_gpg_mapping_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"verify_abu_dhabi_gpg_mapping_item_{index}_title={_truncate(item.title_text)}")
        print(
            f"verify_abu_dhabi_gpg_mapping_item_{index}_due_date="
            f"{_truncate(item.visible_due_date)}"
        )
        print(
            f"verify_abu_dhabi_gpg_mapping_item_{index}_category_label="
            f"{_truncate(item.visible_category_label)}"
        )
        print(
            f"verify_abu_dhabi_gpg_mapping_item_{index}_notice_type="
            f"{_truncate(item.visible_notice_type)}"
        )
        print(
            f"verify_abu_dhabi_gpg_mapping_item_{index}_short_description="
            f"{_truncate(item.visible_short_description)}"
        )
        print(f"verify_abu_dhabi_gpg_mapping_item_{index}_detail_url={item.detail_url}")


def _validate_item(item_index: int, result: AbuDhabiGPGCrawlResult) -> None:
    """Validate deterministic mapping expectations for one homepage widget card."""
    item = result.items[item_index]

    if not item.title_text.strip():
        raise ValueError(f"item {item.item_index} has empty title_text")
    if not item.detail_url.strip():
        raise ValueError(f"item {item.item_index} has empty detail_url")

    parsed = urlparse(item.detail_url)
    if parsed.scheme != "https" or parsed.netloc != "www.adgpg.gov.ae":
        raise ValueError(f"item {item.item_index} detail_url is not on the expected host")
    if parsed.path != "/en/For-Suppliers/Public-Tenders":
        raise ValueError(f"item {item.item_index} detail_url path is unexpected")

    query_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if not query_pairs.get("id"):
        raise ValueError(f"item {item.item_index} detail_url has no non-empty id")

    raw_text = item.raw_text
    if item.title_text not in raw_text:
        raise ValueError(f"item {item.item_index} title_text was not found in raw card text")
    if item.visible_due_date is not None and item.visible_due_date not in raw_text:
        raise ValueError(f"item {item.item_index} visible_due_date was not found in raw card text")
    if (
        item.visible_category_label is not None
        and item.visible_category_label not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} visible_category_label was not found in raw card text"
        )
    if (
        item.visible_short_description is not None
        and item.visible_short_description not in raw_text
    ):
        raise ValueError(
            f"item {item.item_index} visible_short_description was not found in raw card text"
        )
    if item.visible_notice_type is not None:
        title_prefix = item.title_text.split("-", 1)[0].strip()
        if title_prefix != item.visible_notice_type:
            raise ValueError(
                f"item {item.item_index} visible_notice_type does not match the visible title prefix"
            )


async def _run() -> None:
    """Execute row-mapping verification against the live Abu Dhabi GPG homepage widget."""
    result = await run_abu_dhabi_gpg_crawl()

    if result.total_items < 1:
        raise ValueError("expected at least one mapped item, got zero")

    for item_index in range(min(5, result.total_items)):
        _validate_item(item_index, result)

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except AbuDhabiGPGCrawlerError as exc:
        print(
            f"ABU_DHABI_GPG ROW MAPPING VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
