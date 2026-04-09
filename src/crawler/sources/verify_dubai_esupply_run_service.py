from __future__ import annotations

from sqlalchemy import func, select

from src.crawler.sources.dubai_esupply_run_service import run_dubai_esupply_source
from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.db.models.tender import Tender
from src.db.session import get_session_factory

SOURCE_NAME = "Dubai eSupply"


def run() -> None:
    """
    Perform a production-grade persisted verification of the Dubai eSupply run service.

    This script verifies:
    - the source run completes successfully
    - a CrawlRun row is persisted
    - source health fields are updated
    - accepted rows are ingested into tenders
    - ingested tenders have persisted search_text
    - the persisted counts are internally consistent
    """
    session_factory = get_session_factory()

    with session_factory() as session:
        source_before = session.execute(
            select(Source).where(Source.name == SOURCE_NAME)
        ).scalar_one_or_none()

        if source_before is None:
            raise ValueError(
                f"source '{SOURCE_NAME}' was not found; seed sources first"
            )

        before_failure_count = source_before.failure_count
        before_status = source_before.status
        before_last_successful_run_at = source_before.last_successful_run_at
        before_tender_count = len(
            session.execute(
                select(Tender).where(Tender.source_id == source_before.id)
            )
            .scalars()
            .all()
        )

        result = run_dubai_esupply_source(session=session)
        session.commit()

    with session_factory() as session:
        source_after = session.execute(
            select(Source).where(Source.name == SOURCE_NAME)
        ).scalar_one_or_none()

        if source_after is None:
            raise ValueError("source disappeared after run")

        crawl_run = session.get(CrawlRun, result.crawl_run_id)
        if crawl_run is None:
            raise ValueError("expected persisted CrawlRun row was not found")

        tenders_after = (
            session.execute(select(Tender).where(Tender.source_id == source_after.id))
            .scalars()
            .all()
        )
        after_tender_count = len(tenders_after)
        populated_search_text_count = sum(
            1
            for tender in tenders_after
            if isinstance(tender.search_text, str) and tender.search_text.strip()
        )
        duplicate_tender_refs = session.execute(
            select(
                Tender.tender_ref,
                func.count(Tender.id),
            )
            .where(Tender.source_id == source_after.id)
            .where(Tender.tender_ref.is_not(None))
            .group_by(Tender.tender_ref)
            .having(func.count(Tender.id) > 1)
            .order_by(Tender.tender_ref.asc())
        ).all()

        if result.status != "success":
            raise ValueError(f"expected successful source run, got {result.status}")

        if crawl_run.status != "success":
            raise ValueError(
                f"expected persisted crawl_run.status=success, got {crawl_run.status}"
            )

        if crawl_run.source_id != source_after.id:
            raise ValueError("persisted crawl run source_id does not match source")

        if crawl_run.run_identifier != result.run_identifier:
            raise ValueError("persisted crawl run identifier does not match result")

        if source_after.status != "healthy":
            raise ValueError(
                f"expected source status 'healthy', got {source_after.status}"
            )

        if source_after.failure_count != 0:
            raise ValueError(
                f"expected source failure_count=0, got {source_after.failure_count}"
            )

        if source_after.last_successful_run_at is None:
            raise ValueError("expected source.last_successful_run_at to be populated")

        if result.created_tender_count < 0 or result.updated_tender_count < 0:
            raise ValueError("created/updated tender counts must not be negative")

        if result.accepted_row_count != (
            result.created_tender_count + result.updated_tender_count
        ):
            raise ValueError(
                "accepted_row_count does not equal created_tender_count + updated_tender_count"
            )

        if after_tender_count < before_tender_count:
            raise ValueError("tender count decreased unexpectedly after successful run")

        if populated_search_text_count == 0:
            raise ValueError(
                "expected persisted tenders with populated search_text, got zero"
            )

        if duplicate_tender_refs:
            raise ValueError(
                "expected no persisted duplicate tender_ref values, got "
                f"{duplicate_tender_refs[:5]!r}"
            )

        sample_tender_with_search = next(
            (
                tender
                for tender in tenders_after
                if isinstance(tender.search_text, str) and tender.search_text.strip()
            ),
            None,
        )

        if sample_tender_with_search is None:
            raise ValueError("expected at least one tender with populated search_text")

        sample_tender_refs = [
            tender.tender_ref
            for tender in tenders_after
            if isinstance(tender.tender_ref, str) and tender.tender_ref.strip()
        ][:10]

        print(f"verify_run_source_before_status={before_status}")
        print(f"verify_run_source_before_failure_count={before_failure_count}")
        print(
            f"verify_run_source_before_last_successful_run_at={before_last_successful_run_at}"
        )
        print(f"verify_run_before_tender_count={before_tender_count}")
        print(f"verify_run_result_status={result.status}")
        print(f"verify_run_result_run_identifier={result.run_identifier}")
        print(f"verify_run_result_crawled_row_count={result.crawled_row_count}")
        print(f"verify_run_result_normalized_row_count={result.normalized_row_count}")
        print(f"verify_run_result_accepted_row_count={result.accepted_row_count}")
        print(
            f"verify_run_result_review_required_row_count={result.review_required_row_count}"
        )
        print(f"verify_run_result_created_tender_count={result.created_tender_count}")
        print(f"verify_run_result_updated_tender_count={result.updated_tender_count}")
        print(f"verify_run_crawl_run_id={crawl_run.id}")
        print(f"verify_run_crawl_run_status={crawl_run.status}")
        print(f"verify_run_crawl_run_new_tenders_count={crawl_run.new_tenders_count}")
        print(f"verify_run_crawl_run_failure_step={crawl_run.failure_step}")
        print(f"verify_run_crawl_run_failure_reason={crawl_run.failure_reason}")
        print(f"verify_run_source_after_status={source_after.status}")
        print(f"verify_run_source_after_failure_count={source_after.failure_count}")
        print(
            f"verify_run_source_after_last_successful_run_at={source_after.last_successful_run_at.isoformat()}"
        )
        print(f"verify_run_after_tender_count={after_tender_count}")
        print(f"verify_run_populated_search_text_count={populated_search_text_count}")
        print(f"verify_run_duplicate_tender_ref_count={len(duplicate_tender_refs)}")
        print(f"verify_run_sample_tender_refs={sample_tender_refs}")
        print(
            f"verify_run_sample_search_text={sample_tender_with_search.search_text[:120]}"
        )


if __name__ == "__main__":
    run()
