from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from src.operator.source_run_dispatch_service import dispatch_source_run
from src.shared.schemas.operator_run import OperatorRunSourceResponse
from src.shared.schemas.operator_run_batch import OperatorRunAllSourcesResponse

SUPPORTED_SOURCE_RUN_ORDER: tuple[str, str] = (
    "Dubai eSupply",
    "Federal MOF",
)


def run_all_supported_sources(
    *,
    session: Session,
) -> OperatorRunAllSourcesResponse:
    """
    Run all supported sources sequentially in deterministic order.

    Notes:
        - This service does not commit the transaction.
        - The caller owns transaction boundaries.
        - Runs are intentionally sequential for deterministic operational
          behavior and simpler auditability.
        - One source failure does not prevent later sources from running.
    """
    started_at = datetime.now(UTC)
    results: list[OperatorRunSourceResponse] = []

    for source_name in SUPPORTED_SOURCE_RUN_ORDER:
        result = dispatch_source_run(
            session=session,
            source_name=source_name,
        )
        results.append(result)

    finished_at = datetime.now(UTC)
    success_count = sum(1 for result in results if result.status == "success")
    failed_count = len(results) - success_count

    if failed_count == 0:
        overall_status = "success"
    elif success_count == 0:
        overall_status = "failed"
    else:
        overall_status = "partial_failure"

    return OperatorRunAllSourcesResponse(
        started_at=started_at,
        finished_at=finished_at,
        overall_status=overall_status,
        total_sources=len(results),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    )
