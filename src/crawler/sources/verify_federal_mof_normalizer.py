from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from src.crawler.sources.federal_mof_crawler import run_federal_mof_crawl
from src.crawler.sources.federal_mof_normalizer import normalize_federal_mof_rows
from src.db.models.source import Source
from src.db.session import get_session_factory


async def _run() -> None:
    """
    Execute the Federal MOF crawler, query the DB for the source, and 
    verify the deterministic normalization of extracted rows.
    """
    session_factory = get_session_factory()
    with session_factory() as session:
        stmt = select(Source).where(Source.name == "Federal MOF")
        source = session.execute(stmt).scalar_one_or_none()
        if source is None:
            raise ValueError("Federal MOF source not found in database")
        source_id = source.id

    result = await run_federal_mof_crawl()

    if not result.table_rows:
        raise ValueError("Crawler returned no table rows to normalize")

    normalized_rows = normalize_federal_mof_rows(
        source_id=source_id,
        rows=result.table_rows,
    )

    if not normalized_rows:
        raise ValueError("Normalization produced empty result from valid rows")

    first_row = normalized_rows[0]
    if not first_row.title.strip():
        raise ValueError("First normalized row has empty title")
    if not first_row.issuing_entity.strip():
        raise ValueError("First normalized row has empty issuing_entity")
    if not first_row.dedupe_key.strip():
        raise ValueError("First normalized row has empty dedupe_key")
    if first_row.source_id != source_id:
        raise ValueError("First normalized row has mismatched source_id")
    if not first_row.closing_date:
        raise ValueError("First normalized row has missing closing_date")

    print(f"verify_federal_mof_source_name={result.source_name}")
    print(f"verify_federal_mof_listing_url={result.listing_url}")
    print(f"verify_federal_mof_total_crawled_table_rows={result.total_table_rows}")
    print(f"verify_federal_mof_total_normalized_rows={len(normalized_rows)}")
    print(f"verify_federal_mof_first_title={first_row.title}")
    print(f"verify_federal_mof_first_issuing_entity={first_row.issuing_entity}")
    print(f"verify_federal_mof_first_tender_ref={first_row.tender_ref}")
    print(f"verify_federal_mof_first_opening_date={first_row.opening_date.isoformat() if first_row.opening_date else None}")
    print(f"verify_federal_mof_first_closing_date={first_row.closing_date.isoformat()}")
    print(f"verify_federal_mof_first_dedupe_key={first_row.dedupe_key}")


def run() -> None:
    try:
        asyncio.run(_run())
    except Exception as exc:
        print(f"NORMALIZATION VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
