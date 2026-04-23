from __future__ import annotations

import asyncio
import sys

from src.crawler.sources.abu_dhabi_gpg_detail_crawler import (
    AbuDhabiGPGDetailCrawlerError,
    AbuDhabiGPGDetailCrawlResult,
    run_abu_dhabi_gpg_detail_crawl,
)


def _truncate(value: str | None, limit: int = 160) -> str:
    """Return a compact one-line preview for verification output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


def _print_summary(result: AbuDhabiGPGDetailCrawlResult) -> None:
    """Print a compact deterministic summary of sampled detail-page inspection."""
    print(f"verify_abu_dhabi_gpg_detail_source_name={result.source_name}")
    print(f"verify_abu_dhabi_gpg_detail_listing_url={result.listing_url}")
    print(f"verify_abu_dhabi_gpg_detail_final_listing_url={result.final_listing_url}")
    print(f"verify_abu_dhabi_gpg_detail_sample_count={result.sample_count}")
    print(
        "verify_abu_dhabi_gpg_detail_successful_detail_pages="
        f"{result.successful_detail_pages}"
    )
    print(
        f"verify_abu_dhabi_gpg_detail_blocked_page_count={result.blocked_page_count}"
    )
    print(
        f"verify_abu_dhabi_gpg_detail_enrichment_supported={result.enrichment_supported}"
    )

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(
            f"verify_abu_dhabi_gpg_detail_item_{index}_widget_title="
            f"{_truncate(item.widget_title_text)}"
        )
        print(f"verify_abu_dhabi_gpg_detail_item_{index}_detail_url={item.detail_url}")
        print(
            "verify_abu_dhabi_gpg_detail_item_"
            f"{index}_detail_page_title={_truncate(item.detail_page_title)}"
        )
        print(
            f"verify_abu_dhabi_gpg_detail_item_{index}_access_status={item.access_status}"
        )
        print(
            f"verify_abu_dhabi_gpg_detail_item_{index}_detail_title="
            f"{_truncate(item.detail_title)}"
        )
        print(
            "verify_abu_dhabi_gpg_detail_item_"
            f"{index}_detail_issuing_entity={_truncate(item.detail_issuing_entity)}"
        )
        print(
            "verify_abu_dhabi_gpg_detail_item_"
            f"{index}_detail_tender_ref={_truncate(item.detail_tender_ref)}"
        )
        print(
            "verify_abu_dhabi_gpg_detail_item_"
            f"{index}_detail_opening_date_raw={_truncate(item.detail_opening_date_raw)}"
        )
        print(
            "verify_abu_dhabi_gpg_detail_item_"
            f"{index}_detail_closing_date_raw={_truncate(item.detail_closing_date_raw)}"
        )
        print(
            f"verify_abu_dhabi_gpg_detail_item_{index}_detail_category="
            f"{_truncate(item.detail_category)}"
        )
        print(
            "verify_abu_dhabi_gpg_detail_item_"
            f"{index}_detail_notice_type={_truncate(item.detail_notice_type)}"
        )
        print(
            "verify_abu_dhabi_gpg_detail_item_"
            f"{index}_stronger_fields={item.stronger_fields}"
        )
        print(
            f"verify_abu_dhabi_gpg_detail_item_{index}_raw_preview={_truncate(item.raw_text)}"
        )


async def _run() -> None:
    """Execute the live ADGPG detail-page inspection and validate the result shape."""
    result = await run_abu_dhabi_gpg_detail_crawl()

    if result.sample_count < 1:
        raise ValueError("expected at least one sampled detail page, got zero")

    for item in result.items:
        if not item.detail_url.strip():
            raise ValueError(f"detail sample {item.item_index} has empty detail_url")
        if not item.detail_page_title.strip():
            raise ValueError(f"detail sample {item.item_index} has empty detail_page_title")
        if not item.raw_text.strip():
            raise ValueError(f"detail sample {item.item_index} has empty raw_text")
        if item.access_status not in {"detail_page", "blocked_page"}:
            raise ValueError(
                f"detail sample {item.item_index} has unexpected access_status={item.access_status}"
            )
        if item.access_status == "blocked_page" and item.stronger_fields:
            raise ValueError(
                f"detail sample {item.item_index} exposed stronger_fields despite blocked access"
            )
        if item.access_status == "detail_page":
            if item.detail_title is None:
                raise ValueError(
                    f"detail sample {item.item_index} did not expose a visible detail_title"
                )
            if item.detail_closing_date_raw is None:
                raise ValueError(
                    f"detail sample {item.item_index} did not expose a visible closing date"
                )

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except AbuDhabiGPGDetailCrawlerError as exc:
        print(
            f"ABU_DHABI_GPG DETAIL VERIFICATION FAILED: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
