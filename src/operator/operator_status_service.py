from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.shared.schemas.operator_status import (
    OperatorSourceStatusItem,
    OperatorStatusResponse,
)


def list_operator_source_statuses(session: Session) -> OperatorStatusResponse:
    """
    Return an operator-facing health snapshot for all monitored sources.

    Notes:
        - This function is read-only.
        - It does not commit the transaction.
        - It prefers the latest crawl run by started_at desc, then id desc.
    """
    sources = session.execute(
        select(Source).order_by(Source.name.asc(), Source.id.asc())
    ).scalars().all()

    if not sources:
        return OperatorStatusResponse(
            generated_at=datetime.now(timezone.utc),
            sources=[],
        )

    source_ids = [source.id for source in sources]

    crawl_runs = session.execute(
        select(CrawlRun)
        .where(CrawlRun.source_id.in_(source_ids))
        .order_by(
            CrawlRun.source_id.asc(),
            CrawlRun.started_at.desc(),
            CrawlRun.id.desc(),
        )
    ).scalars().all()

    latest_run_by_source_id: dict = {}
    for crawl_run in crawl_runs:
        if crawl_run.source_id not in latest_run_by_source_id:
            latest_run_by_source_id[crawl_run.source_id] = crawl_run

    items = [
        _build_operator_source_status_item(
            source=source,
            latest_run=latest_run_by_source_id.get(source.id),
        )
        for source in sources
    ]

    return OperatorStatusResponse(
        generated_at=datetime.now(timezone.utc),
        sources=items,
    )


def _build_operator_source_status_item(
    *,
    source: Source,
    latest_run: CrawlRun | None,
) -> OperatorSourceStatusItem:
    """Build one operator source status item."""
    return OperatorSourceStatusItem(
        source_id=source.id,
        source_name=source.name,
        source_base_url=source.base_url,
        source_status=source.status,
        failure_count=source.failure_count,
        last_successful_run_at=source.last_successful_run_at,
        last_failed_run_at=source.last_failed_run_at,
        latest_run_id=None if latest_run is None else latest_run.id,
        latest_run_status=None if latest_run is None else latest_run.status,
        latest_run_started_at=None if latest_run is None else latest_run.started_at,
        latest_run_finished_at=None if latest_run is None else latest_run.finished_at,
        latest_run_new_tenders_count=(
            None if latest_run is None else latest_run.new_tenders_count
        ),
        latest_run_failure_reason=(
            None if latest_run is None else latest_run.failure_reason
        ),
        latest_run_failure_step=(
            None if latest_run is None else latest_run.failure_step
        ),
        latest_run_identifier=(
            None if latest_run is None else latest_run.run_identifier
        ),
    )
