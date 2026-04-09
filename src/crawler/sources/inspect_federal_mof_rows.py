from __future__ import annotations

import asyncio

from src.crawler.sources.federal_mof_crawler import run_federal_mof_crawl


async def _run() -> None:
    """
    Inspect the real Federal MOF table row structure before normalization/integration.

    This script is diagnostic-only and exists to verify:
    - actual number of cells per row
    - actual position of reference/entity/title/opening/closing fields
    - whether the current public table is stable enough for deterministic mapping
    """
    result = await run_federal_mof_crawl()

    print(f"inspect_federal_mof_source_name={result.source_name}")
    print(f"inspect_federal_mof_listing_url={result.listing_url}")
    print(f"inspect_federal_mof_total_links={result.total_links}")
    print(f"inspect_federal_mof_total_table_rows={result.total_table_rows}")

    sample_count = min(10, len(result.table_rows))
    for index in range(sample_count):
        row = result.table_rows[index]
        print(f"\n--- FEDERAL_MOF ROW {index + 1} ---")
        print(f"row_index={row.row_index}")
        print(f"cell_count={len(row.cells)}")
        print(f"row_text={row.row_text}")
        for cell_index, cell_value in enumerate(row.cells):
            print(f"cell_{cell_index}={cell_value}")


def run() -> None:
    asyncio.run(_run())

if __name__ == "__main__":
    run()
