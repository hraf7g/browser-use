from __future__ import annotations

import asyncio

from src.crawler.sources.dubai_esupply_crawler import run_dubai_esupply_crawl


async def _run() -> None:
    """
    Inspect the real Dubai eSupply row structure before normalization/integration.

    This script is diagnostic-only and exists to verify:
    - actual number of cells per row
    - actual position of title/reference/date/category fields
    - whether the current normalizer assumptions are correct
    """
    result = await run_dubai_esupply_crawl()

    print(f"inspect_source_name={result.source_name}")
    print(f"inspect_listing_url={result.listing_url}")
    print(f"inspect_total_rows={result.total_rows}")

    sample_count = min(10, len(result.rows))
    for index in range(sample_count):
        row = result.rows[index]
        print(f"\n--- ROW {index + 1} ---")
        print(f"row_index={row.row_index}")
        print(f"cell_count={len(row.cells)}")
        print(f"row_text={row.row_text}")
        for cell_index, cell_value in enumerate(row.cells):
            print(f"cell_{cell_index}={cell_value}")


def run() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    run()
