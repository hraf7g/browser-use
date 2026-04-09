from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from src.crawler.sources.federal_mof_crawler import run_federal_mof_crawl
from src.crawler.sources.federal_mof_normalizer import normalize_federal_mof_rows
from src.crawler.sources.federal_mof_quality import assess_federal_mof_batch_quality
from src.db.models.source import Source
from src.db.session import get_session_factory


async def _run() -> None:
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

    assessments = assess_federal_mof_batch_quality(normalized_rows)

    print(f"verify_federal_mof_total_assessments={len(assessments)}")
    for ix, assessment in enumerate(assessments[:3]):
        print(f"\n--- FEDERAL_MOF ASSESSMENT {ix} ---")
        print(f"title={assessment.payload.title}")
        print(f"issuing_entity={assessment.payload.issuing_entity}")
        print(f"quality_score={assessment.quality_score}")
        print(f"is_review_required={assessment.is_review_required}")
        print(f"quality_flags={assessment.quality_flags}")

def run() -> None:
    try:
        asyncio.run(_run())
    except Exception as exc:
        print(f"QUALITY VERIFICATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
