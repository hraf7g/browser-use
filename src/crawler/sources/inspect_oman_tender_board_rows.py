from __future__ import annotations

import asyncio

from src.crawler.sources.oman_tender_board_crawler import run_oman_tender_board_crawl


async def _run() -> None:
    """
    Inspect the real Oman Tender Board public NewTenders row structure.

    This script is diagnostic-only and exists to verify:
    - actual visible row/cell order
    - whether title, tender number, entity, procurement category, tender type,
      sales-end date, and bid-closing date are stably present on the public table
    - whether the derived public detail URL pattern remains stable
    """
    result = await run_oman_tender_board_crawl()

    print(f"inspect_oman_tender_board_source_name={result.source_name}")
    print(f"inspect_oman_tender_board_listing_url={result.listing_url}")
    print(f"inspect_oman_tender_board_final_url={result.final_url}")
    print(f"inspect_oman_tender_board_page_title={result.page_title}")
    print(f"inspect_oman_tender_board_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"\n--- OMAN_TENDER_BOARD ITEM {index + 1} ---")
        print(f"item_index={item.item_index}")
        print(f"title_text={item.title_text}")
        print(f"visible_tender_number={item.visible_tender_number}")
        print(f"visible_entity={item.visible_entity}")
        print(f"visible_procurement_category={item.visible_procurement_category}")
        print(f"visible_tender_type={item.visible_tender_type}")
        print(f"visible_sales_end_date={item.visible_sales_end_date}")
        print(f"visible_bid_closing_date={item.visible_bid_closing_date}")
        print(f"detail_url={item.detail_url}")
        print(f"raw_text={item.raw_text}")
        for line_index, line in enumerate(item.raw_text.splitlines()):
            print(f"line_{line_index}={line}")


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
