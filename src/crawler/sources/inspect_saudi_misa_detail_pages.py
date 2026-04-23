from __future__ import annotations

import asyncio

from src.crawler.sources.saudi_misa_detail_crawler import run_saudi_misa_detail_crawl


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
    Inspect sampled Saudi MISA-linked Etimad detail pages.

    This script exists to answer whether those detail pages provide stronger
    visible deterministic fields than the MISA table rows.
    """
    result = await run_saudi_misa_detail_crawl()

    print(f"inspect_saudi_misa_detail_source_name={result.source_name}")
    print(f"inspect_saudi_misa_detail_listing_url={result.listing_url}")
    print(f"inspect_saudi_misa_detail_final_listing_url={result.final_listing_url}")
    print(f"inspect_saudi_misa_detail_sample_count={result.sample_count}")
    print(
        "inspect_saudi_misa_detail_successful_detail_pages="
        f"{result.successful_detail_pages}"
    )
    print(f"inspect_saudi_misa_detail_blocked_page_count={result.blocked_page_count}")
    print(
        f"inspect_saudi_misa_detail_enrichment_supported={result.enrichment_supported}"
    )

    for index, item in enumerate(result.items[:5]):
        print(f"\n--- SAUDI_MISA DETAIL ITEM {index + 1} ---")
        print(f"item_index={item.item_index}")
        print(f"table_title={item.table_title_text}")
        print(f"table_reference_number={item.table_reference_number}")
        print(f"table_offer_opening_primary={item.table_offer_opening_primary}")
        print(f"table_offer_opening_secondary={item.table_offer_opening_secondary}")
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
        print(f"detail_procurement_type={item.detail_procurement_type}")
        print(f"detail_description={item.detail_description}")
        print(f"detail_document_indicators={item.detail_document_indicators}")
        print(f"detail_public_action_indicators={item.detail_public_action_indicators}")
        print(f"stronger_fields={item.stronger_fields}")
        print(f"raw_text_preview={_truncate(item.raw_text)}")


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
