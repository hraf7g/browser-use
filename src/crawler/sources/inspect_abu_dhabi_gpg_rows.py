from __future__ import annotations

import asyncio

from src.crawler.sources.abu_dhabi_gpg_crawler import run_abu_dhabi_gpg_crawl


async def _run() -> None:
    """
    Inspect the real Abu Dhabi GPG homepage Active Tenders card structure.

    This script is diagnostic-only and exists to verify:
    - actual visible card field order
    - whether title, due date, category label, notice-type prefix, and short
      description are stably present on the homepage widget
    - whether the homepage-widget-derived public detail URL remains stable
    """
    result = await run_abu_dhabi_gpg_crawl()

    print(f"inspect_abu_dhabi_gpg_source_name={result.source_name}")
    print(f"inspect_abu_dhabi_gpg_listing_url={result.listing_url}")
    print(f"inspect_abu_dhabi_gpg_final_url={result.final_url}")
    print(f"inspect_abu_dhabi_gpg_page_title={result.page_title}")
    print(f"inspect_abu_dhabi_gpg_total_items={result.total_items}")

    sample_count = min(5, len(result.items))
    for index in range(sample_count):
        item = result.items[index]
        print(f"\n--- ABU_DHABI_GPG ITEM {index + 1} ---")
        print(f"item_index={item.item_index}")
        print(f"title_text={item.title_text}")
        print(f"visible_due_date={item.visible_due_date}")
        print(f"visible_category_label={item.visible_category_label}")
        print(f"visible_notice_type={item.visible_notice_type}")
        print(f"visible_short_description={item.visible_short_description}")
        print(f"detail_url={item.detail_url}")
        print(f"raw_text={item.raw_text}")
        for line_index, line in enumerate(item.raw_text.splitlines()):
            print(f"line_{line_index}={line}")


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
