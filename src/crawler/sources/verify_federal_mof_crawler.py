from __future__ import annotations

import asyncio
import sys

from src.crawler.sources.federal_mof_crawler import (
    FederalMOFCrawlerError,
    FederalMOFCrawlResult,
    run_federal_mof_crawl,
)


def _print_summary(result: FederalMOFCrawlResult) -> None:
    """Print a compact verification summary of the crawl result."""
    print(f"verify_federal_mof_source_name={result.source_name}")
    print(f"verify_federal_mof_listing_url={result.listing_url}")
    print(f"verify_federal_mof_page_title={result.page_title}")
    print(f"verify_federal_mof_extracted_at={result.extracted_at.isoformat()}")
    print(f"verify_federal_mof_total_links={result.total_links}")
    print(f"verify_federal_mof_total_table_rows={result.total_table_rows}")

    if result.total_links > 0:
        first_link = result.links[0]
        print(f"verify_federal_mof_first_link_text={first_link.link_text}")
        print(f"verify_federal_mof_first_link_href={first_link.href}")

    if result.total_table_rows > 0:
        first_row = result.table_rows[0]
        print(f"verify_federal_mof_first_row_index={first_row.row_index}")
        print(f"verify_federal_mof_first_row_cell_count={len(first_row.cells)}")
        print(f"verify_federal_mof_first_row_cells={first_row.cells[:5]}")


async def _run() -> None:
    """
    Execute the Federal MOF crawler and validate the result.

    This script verifies:
        - navigation works
        - Arabic/English page markers are found
        - at least one public content artifact is extracted
          (either links or table rows)
    """
    result = await run_federal_mof_crawl()

    if result.total_links < 1 and result.total_table_rows < 1:
        raise ValueError(
            "expected at least one extracted public artifact, got zero links and zero table rows"
        )

    for link in result.links:
        if not (link.link_text and link.link_text.strip()):
            raise ValueError(f"link {link.item_index} has empty link_text")

    for row in result.table_rows:
        if not (row.row_text and row.row_text.strip()):
            raise ValueError(f"row {row.row_index} has empty row_text")
        if not row.cells:
            raise ValueError(f"row {row.row_index} has no cells")

    _print_summary(result)


def run() -> None:
    """Synchronous entrypoint for module execution."""
    try:
        asyncio.run(_run())
    except FederalMOFCrawlerError as exc:
        print(f"FEDERAL_MOF CRAWLER VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
