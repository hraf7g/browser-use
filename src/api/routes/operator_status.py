from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.dependencies.operator_auth import require_operator_api_key
from src.db.session import get_db_session
from src.operator.all_sources_run_service import run_all_supported_sources
from src.operator.operator_status_service import list_operator_source_statuses
from src.operator.source_run_dispatch_service import dispatch_source_run
from src.shared.schemas.operator_run import (
    OperatorRunSourceRequest,
    OperatorRunSourceResponse,
)
from src.shared.schemas.operator_run_batch import OperatorRunAllSourcesResponse
from src.shared.schemas.operator_status import OperatorStatusResponse

router = APIRouter(
    prefix="/operator",
    tags=["operator"],
)


@router.get(
    "/status",
    response_model=OperatorStatusResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_operator_api_key)],
)
def get_operator_status(
    session: Annotated[Session, Depends(get_db_session)],
) -> OperatorStatusResponse:
    """
    Return the operator-facing source health and latest crawl-run snapshot.

    Notes:
        - This route is operator-protected.
        - User auth and operator auth remain intentionally separate.
    """
    return list_operator_source_statuses(session=session)


@router.post(
    "/run-source",
    response_model=OperatorRunSourceResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_operator_api_key)],
)
def post_operator_run_source(
    request: OperatorRunSourceRequest,
    session: Annotated[Session, Depends(get_db_session)],
) -> OperatorRunSourceResponse:
    """
    Run exactly one supported source and persist the resulting crawl metadata.

    Notes:
        - This route is operator-protected.
        - User auth and operator auth remain intentionally separate.
        - The source-specific run service owns crawl/normalize/quality/ingest logic.
        - This route owns the commit boundary so CrawlRun, source health, and
          tender changes persist together.
        - Failed source runs still return a structured 200 response so operators
          can inspect run diagnostics deterministically.
    """
    result = dispatch_source_run(
        session=session,
        source_name=request.source_name,
    )
    session.commit()
    return result


@router.post(
    "/run-all-sources",
    response_model=OperatorRunAllSourcesResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_operator_api_key)],
)
def post_operator_run_all_sources(
    session: Annotated[Session, Depends(get_db_session)],
) -> OperatorRunAllSourcesResponse:
    """
    Run all supported sources sequentially and persist the batch results.

    Notes:
        - This route is operator-protected.
        - User auth and operator auth remain intentionally separate.
        - Source runs are executed sequentially in deterministic order.
        - The route owns the commit boundary so successful source updates persist
          together after the full batch completes.
        - Failed source results remain visible in the structured batch response.
    """
    result = run_all_supported_sources(session=session)
    session.commit()
    return result
