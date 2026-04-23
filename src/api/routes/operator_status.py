from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.ai.control_service import build_ai_control_response, update_ai_control_state
from src.api.dependencies.operator_auth import OperatorAccessContext, require_operator_access
from src.db.session import get_db_session, get_session_factory
from src.operator.all_sources_run_service import (
	run_all_supported_sources_with_isolated_transactions,
)
from src.operator.operator_status_service import list_operator_source_statuses
from src.operator.source_run_dispatch_service import dispatch_source_run
from src.shared.logging.logger import get_logger
from src.shared.schemas.ai_control import (
	AIControlStateResponse,
	AIControlStateUpdateRequest,
)
from src.shared.schemas.operator_run import (
	OperatorRunSourceRequest,
	OperatorRunSourceResponse,
)
from src.shared.schemas.operator_run_batch import OperatorRunAllSourcesResponse
from src.shared.schemas.operator_status import OperatorStatusResponse

router = APIRouter(
	prefix='/operator',
	tags=['operator'],
)
logger = get_logger(__name__)


def _log_operator_action(
	*,
	action: str,
	outcome: str,
	context: OperatorAccessContext,
	**details: object,
) -> None:
	logger.info(
		'operator_action',
		extra={
			'action': action,
			'outcome': outcome,
			'access_path': context.access_path,
			'operator_user_id': context.operator_user_id,
			'operator_email': context.operator_email,
			**details,
		},
	)


@router.get(
	'/status',
	response_model=OperatorStatusResponse,
	status_code=status.HTTP_200_OK,
)
def get_operator_status(
	session: Annotated[Session, Depends(get_db_session)],
	operator_access: Annotated[OperatorAccessContext, Depends(require_operator_access)],
) -> OperatorStatusResponse:
	"""
	Return the operator-facing source health and latest crawl-run snapshot.

	Notes:
	    - This route is operator-protected.
	    - User auth and operator auth remain intentionally separate.
	"""
	try:
		response = list_operator_source_statuses(session=session)
		_log_operator_action(
			action='get_status',
			outcome='success',
			context=operator_access,
			source_count=len(response.sources),
		)
		return response
	except Exception:
		logger.exception(
			'operator_action_failed',
			extra={
				'action': 'get_status',
				'access_path': operator_access.access_path,
				'operator_user_id': operator_access.operator_user_id,
				'operator_email': operator_access.operator_email,
			},
		)
		raise


@router.get(
	'/ai-control',
	response_model=AIControlStateResponse,
	status_code=status.HTTP_200_OK,
)
def get_operator_ai_control(
	session: Annotated[Session, Depends(get_db_session)],
	operator_access: Annotated[OperatorAccessContext, Depends(require_operator_access)],
) -> AIControlStateResponse:
	"""Return the persisted AI control state and effective runtime policy."""
	try:
		response = build_ai_control_response(session)
		_log_operator_action(
			action='get_ai_control',
			outcome='success',
			context=operator_access,
			effective_ai_provider=response.effective_ai_provider,
			effective_ai_enrichment_enabled=response.effective_ai_enrichment_enabled,
		)
		return response
	except Exception:
		logger.exception(
			'operator_action_failed',
			extra={
				'action': 'get_ai_control',
				'access_path': operator_access.access_path,
				'operator_user_id': operator_access.operator_user_id,
				'operator_email': operator_access.operator_email,
			},
		)
		raise


@router.put(
	'/ai-control',
	response_model=AIControlStateResponse,
	status_code=status.HTTP_200_OK,
)
def put_operator_ai_control(
	request: AIControlStateUpdateRequest,
	session: Annotated[Session, Depends(get_db_session)],
	operator_access: Annotated[OperatorAccessContext, Depends(require_operator_access)],
) -> AIControlStateResponse:
	"""Persist an operator-managed AI control update."""
	try:
		response = update_ai_control_state(
			session,
			payload=request,
		)
		session.commit()
		_log_operator_action(
			action='put_ai_control',
			outcome='success',
			context=operator_access,
			ai_enrichment_enabled=response.ai_enrichment_enabled,
			emergency_stop_enabled=response.emergency_stop_enabled,
			effective_ai_enrichment_enabled=response.effective_ai_enrichment_enabled,
		)
		return response
	except Exception:
		session.rollback()
		logger.exception(
			'operator_action_failed',
			extra={
				'action': 'put_ai_control',
				'access_path': operator_access.access_path,
				'operator_user_id': operator_access.operator_user_id,
				'operator_email': operator_access.operator_email,
			},
		)
		raise


@router.post(
	'/run-source',
	response_model=OperatorRunSourceResponse,
	status_code=status.HTTP_200_OK,
)
def post_operator_run_source(
	request: OperatorRunSourceRequest,
	session: Annotated[Session, Depends(get_db_session)],
	operator_access: Annotated[OperatorAccessContext, Depends(require_operator_access)],
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
	try:
		result = dispatch_source_run(
			session=session,
			source_name=request.source_name,
		)
		session.commit()
		_log_operator_action(
			action='run_source',
			outcome='success',
			context=operator_access,
			source_name=request.source_name,
			run_status=result.status,
		)
		return result
	except Exception:
		session.rollback()
		logger.exception(
			'operator_action_failed',
			extra={
				'action': 'run_source',
				'access_path': operator_access.access_path,
				'operator_user_id': operator_access.operator_user_id,
				'operator_email': operator_access.operator_email,
				'source_name': request.source_name,
			},
		)
		raise


@router.post(
	'/run-all-sources',
	response_model=OperatorRunAllSourcesResponse,
	status_code=status.HTTP_200_OK,
)
def post_operator_run_all_sources(
	operator_access: Annotated[OperatorAccessContext, Depends(require_operator_access)],
) -> OperatorRunAllSourcesResponse:
	"""
	Run all supported sources sequentially and persist the batch results.

	Notes:
	    - This route is operator-protected.
	    - User auth and operator auth remain intentionally separate.
	    - Source runs are executed sequentially in deterministic order.
	    - Each source persists in its own transaction so a later unexpected failure
	      does not roll back earlier successful source runs.
	    - Failed source results remain visible in the structured batch response.
	"""
	try:
		response = run_all_supported_sources_with_isolated_transactions(
			session_factory=get_session_factory(),
		)
		_log_operator_action(
			action='run_all_sources',
			outcome='success',
			context=operator_access,
			source_count=len(response.results),
		)
		return response
	except Exception:
		logger.exception(
			'operator_action_failed',
			extra={
				'action': 'run_all_sources',
				'access_path': operator_access.access_path,
				'operator_user_id': operator_access.operator_user_id,
				'operator_email': operator_access.operator_email,
			},
		)
		raise
