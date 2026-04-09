from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.db.session import get_session_factory
from src.operator.operator_status_service import list_operator_source_statuses


def run() -> None:
    """
    Perform an isolated production-grade verification of the operator status service.

    This script verifies:
    - sources can be read
    - a staged crawl run becomes the latest run for the selected source
    - the operator status service returns the expected latest run metadata
    - verification does not permanently mutate production data
    """
    session_factory = get_session_factory()
    verification_run_identifier = f"verify-operator-{uuid4().hex}"

    with session_factory() as session:
        source = session.execute(
            select(Source).order_by(Source.name.asc(), Source.id.asc())
        ).scalars().first()

        if source is None:
            raise ValueError("no sources were found; seed sources first")

        now = datetime.now(timezone.utc)

        staged_crawl_run = CrawlRun(
            source_id=source.id,
            status="success",
            started_at=now,
            finished_at=now,
            new_tenders_count=1,
            failure_reason=None,
            failure_step=None,
            run_identifier=verification_run_identifier,
        )
        session.add(staged_crawl_run)
        session.flush()

        response = list_operator_source_statuses(session=session)

        source_item = next(
            (item for item in response.sources if item.source_id == source.id),
            None,
        )

        if source_item is None:
            raise ValueError("expected source item was not returned by operator status service")

        if source_item.latest_run_identifier != verification_run_identifier:
            raise ValueError(
                "operator status service did not return the staged crawl run as latest"
            )

        if source_item.latest_run_status != "success":
            raise ValueError(
                f"expected latest_run_status 'success', got {source_item.latest_run_status}"
            )

        if source_item.latest_run_new_tenders_count != 1:
            raise ValueError(
                "operator status service did not return the expected new_tenders_count"
            )

        print(f"verify_operator_generated_at={response.generated_at.isoformat()}")
        print(f"verify_operator_source_id={source_item.source_id}")
        print(f"verify_operator_source_name={source_item.source_name}")
        print(f"verify_operator_source_status={source_item.source_status}")
        print(f"verify_operator_failure_count={source_item.failure_count}")
        print(f"verify_operator_latest_run_id={source_item.latest_run_id}")
        print(f"verify_operator_latest_run_status={source_item.latest_run_status}")
        print(
            f"verify_operator_latest_run_started_at={source_item.latest_run_started_at.isoformat()}"
        )
        print(
            f"verify_operator_latest_run_finished_at={source_item.latest_run_finished_at.isoformat()}"
        )
        print(
            f"verify_operator_latest_run_new_tenders_count={source_item.latest_run_new_tenders_count}"
        )
        print(
            f"verify_operator_latest_run_identifier={source_item.latest_run_identifier}"
        )

        session.rollback()


if __name__ == "__main__":
    run()
