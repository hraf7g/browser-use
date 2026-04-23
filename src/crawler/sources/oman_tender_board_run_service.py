from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.crawler.sources.oman_tender_board_crawler import (
    OmanTenderBoardCrawlerError,
    run_oman_tender_board_crawl,
)
from src.crawler.sources.oman_tender_board_normalizer import (
    OmanTenderBoardNormalizationError,
    normalize_oman_tender_board_items,
)
from src.crawler.sources.oman_tender_board_quality import (
    assess_oman_tender_board_payloads,
)
from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.ingestion.tender_ingestion_service import ingest_tender

SOURCE_NAME: Final[str] = "Oman Tender Board"
MAX_FAILURE_REASON_LENGTH: Final[int] = 2000


class OmanTenderBoardSourceRunError(ValueError):
    """Raised when the Oman Tender Board source cannot be initialized."""


@dataclass(frozen=True)
class OmanTenderBoardSourceRunResult:
    """Structured result for one full Oman Tender Board source run."""

    source_name: str
    source_id: UUID
    crawl_run_id: UUID
    run_identifier: str
    status: str
    started_at: datetime
    finished_at: datetime
    crawled_row_count: int
    normalized_row_count: int
    accepted_row_count: int
    review_required_row_count: int
    created_tender_count: int
    updated_tender_count: int
    failure_step: str | None = None
    failure_reason: str | None = None


def run_oman_tender_board_source(session: Session) -> OmanTenderBoardSourceRunResult:
    """
    Run the Oman Tender Board source end-to-end.

    Flow:
        - live crawl
        - normalization
        - deterministic quality assessment
        - ingest accepted rows only
        - write CrawlRun metadata
        - update Source health fields

    Notes:
        - This function does not commit the transaction.
        - The caller owns transaction boundaries.
        - Accepted-row ingestion is wrapped in a nested transaction so partial
          tender writes are rolled back if ingestion fails mid-run.
        - Review-required rows are counted but not ingested in this step.
    """
    source = _get_source(session=session)
    started_at = datetime.now(UTC)
    run_identifier = f"oman-tender-board-{uuid4().hex}"

    crawled_row_count = 0
    normalized_row_count = 0
    accepted_row_count = 0
    review_required_row_count = 0
    created_tender_count = 0
    updated_tender_count = 0

    try:
        crawl_result = asyncio.run(run_oman_tender_board_crawl())
        crawled_row_count = crawl_result.total_items

        normalized_rows = normalize_oman_tender_board_items(
            source_id=source.id,
            items=crawl_result.items,
        )
        normalized_row_count = len(normalized_rows)

        assessments = assess_oman_tender_board_payloads(normalized_rows)
        accepted_assessments = [
            assessment for assessment in assessments if not assessment.is_review_required
        ]
        review_required_assessments = [
            assessment for assessment in assessments if assessment.is_review_required
        ]

        accepted_row_count = len(accepted_assessments)
        review_required_row_count = len(review_required_assessments)

        with session.begin_nested():
            for assessment in accepted_assessments:
                tender, created = ingest_tender(
                    session=session,
                    payload=assessment.payload,
                )
                _validate_ingested_tender_search_text(tender.search_text)

                if created:
                    created_tender_count += 1
                else:
                    updated_tender_count += 1

        finished_at = datetime.now(UTC)

        crawl_run = CrawlRun(
            source_id=source.id,
            status="success",
            started_at=started_at,
            finished_at=finished_at,
            new_tenders_count=created_tender_count,
            crawled_row_count=crawled_row_count,
            normalized_row_count=normalized_row_count,
            accepted_row_count=accepted_row_count,
            review_required_row_count=review_required_row_count,
            updated_tender_count=updated_tender_count,
            failure_reason=None,
            failure_step=None,
            run_identifier=run_identifier,
        )
        session.add(crawl_run)

        source.status = "healthy"
        source.failure_count = 0
        source.last_successful_run_at = finished_at

        session.flush()

        return OmanTenderBoardSourceRunResult(
            source_name=SOURCE_NAME,
            source_id=source.id,
            crawl_run_id=crawl_run.id,
            run_identifier=run_identifier,
            status="success",
            started_at=started_at,
            finished_at=finished_at,
            crawled_row_count=crawled_row_count,
            normalized_row_count=normalized_row_count,
            accepted_row_count=accepted_row_count,
            review_required_row_count=review_required_row_count,
            created_tender_count=created_tender_count,
            updated_tender_count=updated_tender_count,
            failure_step=None,
            failure_reason=None,
        )

    except Exception as exc:
        finished_at = datetime.now(UTC)
        failure_step = _classify_failure_step(exc)
        failure_reason = _truncate_failure_reason(str(exc))

        crawl_run = CrawlRun(
            source_id=source.id,
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            new_tenders_count=0,
            crawled_row_count=crawled_row_count,
            normalized_row_count=normalized_row_count,
            accepted_row_count=accepted_row_count,
            review_required_row_count=review_required_row_count,
            updated_tender_count=0,
            failure_reason=failure_reason,
            failure_step=failure_step,
            run_identifier=run_identifier,
        )
        session.add(crawl_run)

        source.status = "degraded"
        source.failure_count += 1
        source.last_failed_run_at = finished_at

        session.flush()

        return OmanTenderBoardSourceRunResult(
            source_name=SOURCE_NAME,
            source_id=source.id,
            crawl_run_id=crawl_run.id,
            run_identifier=run_identifier,
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            crawled_row_count=crawled_row_count,
            normalized_row_count=normalized_row_count,
            accepted_row_count=accepted_row_count,
            review_required_row_count=review_required_row_count,
            created_tender_count=0,
            updated_tender_count=0,
            failure_step=failure_step,
            failure_reason=failure_reason,
        )


def _get_source(session: Session) -> Source:
    """Load the Oman Tender Board source from the database."""
    source = session.execute(
        select(Source).where(Source.name == SOURCE_NAME)
    ).scalar_one_or_none()
    if source is None:
        raise OmanTenderBoardSourceRunError(
            f"source '{SOURCE_NAME}' was not found; seed sources first"
        )
    return source


def _validate_ingested_tender_search_text(search_text: str) -> None:
    """Fail fast if persisted search text is blank."""
    if not isinstance(search_text, str) or not search_text.strip():
        raise ValueError("ingested tender search_text is unexpectedly empty")


def _classify_failure_step(exc: Exception) -> str:
    """Classify failure stage for crawl-run diagnostics."""
    if isinstance(exc, OmanTenderBoardCrawlerError):
        return "crawl"
    if isinstance(exc, OmanTenderBoardNormalizationError):
        return "normalize"
    return "ingest_or_unknown"


def _truncate_failure_reason(value: str) -> str:
    """Bound failure-reason size for safer persistence."""
    cleaned = value.strip()
    if len(cleaned) <= MAX_FAILURE_REASON_LENGTH:
        return cleaned
    return cleaned[:MAX_FAILURE_REASON_LENGTH]
