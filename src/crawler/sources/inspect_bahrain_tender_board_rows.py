from __future__ import annotations

import asyncio

from src.crawler.sources.bahrain_tender_board_crawler import (
    run_bahrain_tender_board_crawl,
)


async def _run() -> None:
    """
    Inspect the real Bahrain Tender Board dashboard row structure before normalization.

    This script is diagnostic-only and exists to verify:
    - actual visible dashboard row/cell order
    - whether title, tender number, PA reference, entity, and time-left text
      are stably present on the public dashboard
    - whether the derived public detail URL pattern remains stable
    """
    result = await run_bahrain_tender_board_crawl()

    print(f"inspect_bahrain_tender_board_source_name={result.source_name}")
    print(f"inspect_bahrain_tender_board_listing_url={result.listing_url}")
    print(f"inspect_bahrain_tender_board_final_url={result.final_url}")
    print(f"inspect_bahrain_tender_board_page_title={result.page_title}")
    print(f"inspect_bahrain_tender_board_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"\n--- BAHRAIN_TENDER_BOARD ITEM {index + 1} ---")
        print(f"item_index={item.item_index}")
        print(f"title_text={item.title_text}")
        print(f"visible_tender_number={item.visible_tender_number}")
        print(f"visible_pa_reference={item.visible_pa_reference}")
        print(f"visible_entity={item.visible_entity}")
        print(f"visible_time_left={item.visible_time_left}")
        print(f"detail_url={item.detail_url}")
        print(f"raw_text={item.raw_text}")
        for line_index, line in enumerate(item.raw_text.splitlines()):
            print(f"line_{line_index}={line}")


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
