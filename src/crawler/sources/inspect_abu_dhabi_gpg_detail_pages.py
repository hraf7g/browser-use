from __future__ import annotations

import asyncio

from src.crawler.sources.abu_dhabi_gpg_detail_crawler import (
    run_abu_dhabi_gpg_detail_crawl,
)


def _truncate(value: str | None, limit: int = 240) -> str:
    """Return a compact single-line preview for inspection output."""
    if value is None:
        return "None"
    compact = value.replace("\n", " | ").strip()
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."


async def _run() -> None:
    """
    Inspect sampled Abu Dhabi GPG public detail pages.

    This script exists to answer whether the detail pages provide stronger visible
    deterministic fields than the homepage widget cards.
    """
    result = await run_abu_dhabi_gpg_detail_crawl()

    print(f"inspect_abu_dhabi_gpg_detail_source_name={result.source_name}")
    print(f"inspect_abu_dhabi_gpg_detail_listing_url={result.listing_url}")
    print(f"inspect_abu_dhabi_gpg_detail_final_listing_url={result.final_listing_url}")
    print(f"inspect_abu_dhabi_gpg_detail_sample_count={result.sample_count}")
    print(
        "inspect_abu_dhabi_gpg_detail_successful_detail_pages="
        f"{result.successful_detail_pages}"
    )
    print(
        f"inspect_abu_dhabi_gpg_detail_blocked_page_count={result.blocked_page_count}"
    )
    print(
        f"inspect_abu_dhabi_gpg_detail_enrichment_supported={result.enrichment_supported}"
    )

    for index, item in enumerate(result.items[:5]):
        print(f"\n--- ABU_DHABI_GPG DETAIL ITEM {index + 1} ---")
        print(f"item_index={item.item_index}")
        print(f"widget_title={item.widget_title_text}")
        print(f"widget_due_date={item.widget_visible_due_date}")
        print(f"widget_notice_type={item.widget_visible_notice_type}")
        print(f"detail_url={item.detail_url}")
        print(f"final_url={item.final_url}")
        print(f"detail_page_title={item.detail_page_title}")
        print(f"access_status={item.access_status}")
        print(f"detail_title={item.detail_title}")
        print(f"detail_issuing_entity={item.detail_issuing_entity}")
        print(f"detail_tender_ref={item.detail_tender_ref}")
        print(f"detail_published_at_raw={item.detail_published_at_raw}")
        print(f"detail_opening_date_raw={item.detail_opening_date_raw}")
        print(f"detail_closing_date_raw={item.detail_closing_date_raw}")
        print(f"detail_category={item.detail_category}")
        print(f"detail_notice_type={item.detail_notice_type}")
        print(f"detail_description={item.detail_description}")
        print(f"detail_document_indicators={item.detail_document_indicators}")
        print(f"detail_public_action_indicators={item.detail_public_action_indicators}")
        print(f"stronger_fields={item.stronger_fields}")
        print(f"raw_text_preview={_truncate(item.raw_text)}")


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
