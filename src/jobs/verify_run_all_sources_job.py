from __future__ import annotations

from sqlalchemy import select

from src.db.models.crawl_run import CrawlRun
from src.db.session import get_session_factory
from src.jobs.run_all_sources_job_service import run_all_sources_job


def run() -> None:
    """
    Perform a persisted verification of the all-sources batch job service.

    This script verifies:
        - the job returns a structured overall status
        - exactly six source results are returned
        - all supported source names are present
        - persisted CrawlRun rows exist for each returned run_identifier
    """
    result = run_all_sources_job()

    if not result.overall_status:
        raise ValueError("expected overall_status to be populated")

    if result.total_sources != 6:
        raise ValueError(f"expected total_sources=6, got {result.total_sources}")

    if len(result.results) != 6:
        raise ValueError(f"expected exactly 6 source results, got {len(result.results)}")

    ordered_source_names = [item.source_name for item in result.results]
    expected_source_names = [
        "Dubai eSupply",
        "Federal MOF",
        "Saudi Etimad",
        "Saudi MISA Procurements",
        "Oman Tender Board",
        "Abu Dhabi GPG",
    ]
    if ordered_source_names != expected_source_names:
        raise ValueError(
            f"expected ordered source names {expected_source_names!r}, got {ordered_source_names!r}"
        )

    session_factory = get_session_factory()
    with session_factory() as session:
        crawl_runs = session.execute(
            select(CrawlRun).where(
                CrawlRun.run_identifier.in_(
                    [item.run_identifier for item in result.results]
                )
            )
        ).scalars().all()

    if len(crawl_runs) != 6:
        raise ValueError(
            "expected persisted CrawlRun rows for all returned run identifiers, "
            f"got {len(crawl_runs)}"
        )

    persisted_identifiers = {crawl_run.run_identifier for crawl_run in crawl_runs}
    missing_identifiers = {
        item.run_identifier for item in result.results
    } - persisted_identifiers
    if missing_identifiers:
        raise ValueError(
            "missing persisted CrawlRun rows for run identifiers "
            f"{sorted(missing_identifiers)!r}"
        )

    print(f"verify_run_all_sources_job_overall_status={result.overall_status}")
    print(f"verify_run_all_sources_job_total_sources={result.total_sources}")
    print(f"verify_run_all_sources_job_success_count={result.success_count}")
    print(f"verify_run_all_sources_job_failed_count={result.failed_count}")
    print(f"verify_run_all_sources_job_results_count={len(result.results)}")

    for item in result.results:
        print(
            "verify_run_all_sources_job_result="
            f"{item.source_name}|{item.status}|{item.run_identifier}|"
            f"{item.created_tender_count}|{item.updated_tender_count}"
        )


if __name__ == "__main__":
    run()
