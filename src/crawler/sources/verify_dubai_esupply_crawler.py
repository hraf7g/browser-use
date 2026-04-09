from __future__ import annotations

import asyncio
import sys

from src.crawler.sources.dubai_esupply_crawler import (
    DubaiESupplyCrawlResult,
    DubaiESupplyCrawlerError,
    run_dubai_esupply_crawl,
)


def _print_summary(result: DubaiESupplyCrawlResult) -> None:
    """Print a compact verification summary of the crawl result."""
    print(f"verify_crawler_source_name={result.source_name}")
    print(f"verify_crawler_listing_url={result.listing_url}")
    print(f"verify_crawler_page_title={result.page_title}")
    print(f"verify_crawler_extracted_at={result.extracted_at.isoformat()}")
    print(f"verify_crawler_total_rows={result.total_rows}")

    if result.total_rows == 0:
        print("verify_crawler_sample_row=NONE")
        return

    first_row = result.rows[0]
    print(f"verify_crawler_first_row_index={first_row.row_index}")
    print(f"verify_crawler_first_row_cell_count={len(first_row.cells)}")
    print(f"verify_crawler_first_row_cells={first_row.cells[:5]}")

    if result.total_rows > 1:
        last_row = result.rows[-1]
        print(f"verify_crawler_last_row_index={last_row.row_index}")
        print(f"verify_crawler_last_row_cell_count={len(last_row.cells)}")
        print(f"verify_crawler_last_row_cells={last_row.cells[:5]}")


async def _run() -> None:
    """Execute the crawler and validate the result."""
    result = await run_dubai_esupply_crawl()

    if result.total_rows < 1:
        raise ValueError("expected at least one extracted row, got zero")

    for row in result.rows:
        if not row.cells:
            raise ValueError(f"row {row.row_index} has no cells")
        if not row.row_text:
            raise ValueError(f"row {row.row_index} has empty row_text")

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except DubaiESupplyCrawlerError as exc:
        print(f"CRAWLER VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
