from __future__ import annotations

import asyncio

from src.crawler.sources.saudi_etimad_crawler import run_saudi_etimad_crawl


async def _run() -> None:
    """
    Inspect the real Saudi Etimad listing-card structure before normalization.

    This script is diagnostic-only and exists to verify:
    - actual visible line order inside listing cards
    - whether title/entity/date/type are stably present on the listing page
    - whether visible reference text exists separately or only inside titles
    """
    result = await run_saudi_etimad_crawl()

    print(f"inspect_saudi_etimad_source_name={result.source_name}")
    print(f"inspect_saudi_etimad_listing_url={result.listing_url}")
    print(f"inspect_saudi_etimad_final_url={result.final_url}")
    print(f"inspect_saudi_etimad_page_title={result.page_title}")
    print(f"inspect_saudi_etimad_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"\n--- SAUDI_ETIMAD ITEM {index + 1} ---")
        print(f"item_index={item.item_index}")
        print(f"title_text={item.title_text}")
        print(f"issuing_entity={item.issuing_entity}")
        print(f"publication_date={item.publication_date}")
        print(f"procurement_type_label={item.procurement_type_label}")
        print(f"visible_reference={item.visible_reference}")
        print(f"detail_url={item.detail_url}")
        print(f"reference_fields={item.reference_fields}")
        print(f"date_fields={item.date_fields}")
        print(f"raw_text={item.raw_text}")
        for line_index, line in enumerate(item.raw_text.splitlines()):
            print(f"line_{line_index}={line}")


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
