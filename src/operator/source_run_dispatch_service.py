from __future__ import annotations

from sqlalchemy.orm import Session

from src.crawler.sources.dubai_esupply_run_service import run_dubai_esupply_source
from src.crawler.sources.federal_mof_run_service import run_federal_mof_source
from src.shared.schemas.operator_run import (
    OperatorRunSourceResponse,
    SupportedOperatorSourceName,
)


class SourceRunDispatchError(ValueError):
    """Raised when a manual source run cannot be dispatched safely."""


def dispatch_source_run(
    *,
    session: Session,
    source_name: str,
) -> OperatorRunSourceResponse:
    """
    Dispatch one supported manual source run and normalize the result.

    Notes:
        - This service does not commit the transaction.
        - The caller owns transaction boundaries.
        - Only explicitly supported sources can be triggered.
        - Source-specific run services remain authoritative for crawl logic.
    """
    normalized_source_name = source_name.strip()

    if normalized_source_name == "Dubai eSupply":
        result = run_dubai_esupply_source(session=session)
        return OperatorRunSourceResponse(
            source_name="Dubai eSupply",
            source_id=result.source_id,
            crawl_run_id=result.crawl_run_id,
            run_identifier=result.run_identifier,
            status=result.status,
            started_at=result.started_at,
            finished_at=result.finished_at,
            crawled_row_count=result.crawled_row_count,
            normalized_row_count=result.normalized_row_count,
            accepted_row_count=result.accepted_row_count,
            review_required_row_count=result.review_required_row_count,
            created_tender_count=result.created_tender_count,
            updated_tender_count=result.updated_tender_count,
            failure_step=result.failure_step,
            failure_reason=result.failure_reason,
        )

    if normalized_source_name == "Federal MOF":
        result = run_federal_mof_source(session=session)
        return OperatorRunSourceResponse(
            source_name="Federal MOF",
            source_id=result.source_id,
            crawl_run_id=result.crawl_run_id,
            run_identifier=result.run_identifier,
            status=result.status,
            started_at=result.started_at,
            finished_at=result.finished_at,
            crawled_row_count=result.crawled_row_count,
            normalized_row_count=result.normalized_row_count,
            accepted_row_count=result.accepted_row_count,
            review_required_row_count=result.review_required_row_count,
            created_tender_count=result.created_tender_count,
            updated_tender_count=result.updated_tender_count,
            failure_step=result.failure_step,
            failure_reason=result.failure_reason,
        )

    raise SourceRunDispatchError(
        "unsupported source_name for manual operator run: "
        f"{normalized_source_name!r}; supported values are "
        f"{_supported_source_names_text()}"
    )


def _supported_source_names_text() -> str:
    """Return the allowed manual-run source names for diagnostics."""
    supported_names: tuple[SupportedOperatorSourceName, ...] = (
        "Dubai eSupply",
        "Federal MOF",
    )
    return ", ".join(f"'{name}'" for name in supported_names)
