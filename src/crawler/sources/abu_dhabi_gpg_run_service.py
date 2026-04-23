from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.crawler.sources.abu_dhabi_gpg_crawler import (
    AbuDhabiGPGCrawlerError,
    run_abu_dhabi_gpg_crawl,
)
from src.crawler.sources.abu_dhabi_gpg_detail_crawler import (
    AbuDhabiGPGDetailCrawlerError,
    run_abu_dhabi_gpg_detail_crawl,
)
from src.crawler.sources.abu_dhabi_gpg_enriched_normalizer import (
    AbuDhabiGPGEnrichedNormalizationError,
    normalize_abu_dhabi_gpg_enriched_items,
)
from src.crawler.sources.abu_dhabi_gpg_enriched_quality import (
    assess_abu_dhabi_gpg_enriched_payloads,
)
from src.db.models.crawl_run import CrawlRun
from src.db.models.source import Source
from src.ingestion.tender_ingestion_service import ingest_tender

SOURCE_NAME: Final[str] = "Abu Dhabi GPG"
MAX_FAILURE_REASON_LENGTH: Final[int] = 2000


class AbuDhabiGPGSourceRunError(ValueError):
    """Raised when the Abu Dhabi GPG source cannot be initialized."""


@dataclass(frozen=True)
class AbuDhabiGPGSourceRunResult:
    """Structured result for one full Abu Dhabi GPG enriched source run."""

    source_name: str
    source_id: UUID
    crawl_run_id: UUID
    run_identifier: str
    status: str
    started_at: datetime
    finished_at: datetime
    widget_crawled_row_count: int
    detail_sampled_row_count: int
    enriched_normalized_row_count: int
    accepted_row_count: int
    review_required_row_count: int
    created_tender_count: int
    updated_tender_count: int
    failure_step: str | None = None
    failure_reason: str | None = None


def run_abu_dhabi_gpg_source(session: Session) -> AbuDhabiGPGSourceRunResult:
    """
    Run the Abu Dhabi GPG enriched source end-to-end.

    Flow:
        - live widget crawl
        - live detail-page enrichment
        - enriched normalization
        - deterministic enriched quality assessment
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
    run_identifier = f"abu-dhabi-gpg-{uuid4().hex}"

    widget_crawled_row_count = 0
    detail_sampled_row_count = 0
    enriched_normalized_row_count = 0
    accepted_row_count = 0
    review_required_row_count = 0
    created_tender_count = 0
    updated_tender_count = 0

    try:
        widget_result = asyncio.run(run_abu_dhabi_gpg_crawl())
        widget_crawled_row_count = widget_result.total_items

        detail_result = asyncio.run(
            run_abu_dhabi_gpg_detail_crawl(
                sample_size=None,
                widget_items=widget_result.items,
                jitter_range_ms=(1500, 2500),
            )
        )
        detail_sampled_row_count = len(detail_result.items)

        normalized_rows = normalize_abu_dhabi_gpg_enriched_items(
            source_id=source.id,
            items=detail_result.items,
        )
        enriched_normalized_row_count = len(normalized_rows)

        assessments = assess_abu_dhabi_gpg_enriched_payloads(normalized_rows)
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
            crawled_row_count=widget_crawled_row_count,
            normalized_row_count=enriched_normalized_row_count,
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

        return AbuDhabiGPGSourceRunResult(
            source_name=SOURCE_NAME,
            source_id=source.id,
            crawl_run_id=crawl_run.id,
            run_identifier=run_identifier,
            status="success",
            started_at=started_at,
            finished_at=finished_at,
            widget_crawled_row_count=widget_crawled_row_count,
            detail_sampled_row_count=detail_sampled_row_count,
            enriched_normalized_row_count=enriched_normalized_row_count,
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
            crawled_row_count=widget_crawled_row_count,
            normalized_row_count=enriched_normalized_row_count,
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

        return AbuDhabiGPGSourceRunResult(
            source_name=SOURCE_NAME,
            source_id=source.id,
            crawl_run_id=crawl_run.id,
            run_identifier=run_identifier,
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            widget_crawled_row_count=widget_crawled_row_count,
            detail_sampled_row_count=detail_sampled_row_count,
            enriched_normalized_row_count=enriched_normalized_row_count,
            accepted_row_count=accepted_row_count,
            review_required_row_count=review_required_row_count,
            created_tender_count=0,
            updated_tender_count=0,
            failure_step=failure_step,
            failure_reason=failure_reason,
        )


def _get_source(session: Session) -> Source:
    """Load the Abu Dhabi GPG source from the database."""
    source = session.execute(
        select(Source).where(Source.name == SOURCE_NAME)
    ).scalar_one_or_none()
    if source is None:
        raise AbuDhabiGPGSourceRunError(
            f"source '{SOURCE_NAME}' was not found; seed sources first"
        )
    return source


def _validate_ingested_tender_search_text(search_text: str) -> None:
    """Fail fast if persisted search text is blank."""
    if not isinstance(search_text, str) or not search_text.strip():
        raise ValueError("ingested tender search_text is unexpectedly empty")


def _classify_failure_step(exc: Exception) -> str:
    """Classify failure stage for crawl-run diagnostics."""
    if isinstance(exc, AbuDhabiGPGCrawlerError):
        return "widget_crawl"
    if isinstance(exc, AbuDhabiGPGDetailCrawlerError):
        return "detail_enrichment"
    if isinstance(exc, AbuDhabiGPGEnrichedNormalizationError):
        return "normalize"
    return "ingest_or_unknown"


def _truncate_failure_reason(value: str) -> str:
    """Bound failure-reason size for safer persistence."""
    cleaned = value.strip()
    if len(cleaned) <= MAX_FAILURE_REASON_LENGTH:
        return cleaned
    return cleaned[:MAX_FAILURE_REASON_LENGTH]
