from __future__ import annotations

import asyncio

from src.crawler.sources.saudi_misa_crawler import run_saudi_misa_crawl


async def _run() -> None:
    """
    Inspect the real Saudi MISA procurements table row structure.

    This script is diagnostic-only and exists to verify:
    - actual visible competitions-table cell order
    - whether title, reference number, offering date, inquiry deadline, bid
      deadline, and visible Etimad visitor detail link remain stably present
      on the public table
    - whether the Etimad detail URL remains stable across visible rows
    """
    result = await run_saudi_misa_crawl()

    print(f"inspect_saudi_misa_source_name={result.source_name}")
    print(f"inspect_saudi_misa_listing_url={result.listing_url}")
    print(f"inspect_saudi_misa_final_url={result.final_url}")
    print(f"inspect_saudi_misa_page_title={result.page_title}")
    print(f"inspect_saudi_misa_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"\n--- SAUDI_MISA ITEM {index + 1} ---")
        print(f"item_index={item.item_index}")
        print(f"title_text={item.title_text}")
        print(f"detail_url={item.detail_url}")
        print(f"visible_reference_number={item.visible_reference_number}")
        print(f"visible_offering_date={item.visible_offering_date}")
        print(f"visible_inquiry_deadline={item.visible_inquiry_deadline}")
        print(f"visible_bid_deadline={item.visible_bid_deadline}")
        print(f"visible_status_link_text={item.visible_status_link_text}")
        print(f"raw_text={item.raw_text}")
        for line_index, line in enumerate(item.raw_text.splitlines()):
            print(f"line_{line_index}={line}")


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
