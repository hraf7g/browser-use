from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user
from src.browser_agent.service import (
	BrowserAgentAdmissionError,
	BrowserAgentRunAlreadyFinishedError,
	BrowserAgentRunNotFoundError,
	list_browser_agent_runs_for_user,
	queue_browser_agent_run,
	request_browser_agent_run_cancellation,
)
from src.db.models.user import User
from src.db.session import get_db_session
from src.shared.schemas.browser_agent import (
	BrowserAgentCancelResponse,
	BrowserAgentRunCreateRequest,
	BrowserAgentRunListResponse,
	BrowserAgentRunResponse,
)

router = APIRouter(
	prefix='/browser-agent-runs',
	tags=['browser-agent'],
)


@router.get(
	'',
	response_model=BrowserAgentRunListResponse,
	status_code=status.HTTP_200_OK,
)
def get_browser_agent_runs(
	session: Annotated[Session, Depends(get_db_session)],
	current_user: Annotated[User, Depends(get_current_user)],
) -> BrowserAgentRunListResponse:
	"""Return recent browser-agent runs for the current user."""
	return list_browser_agent_runs_for_user(session, user_id=current_user.id)


@router.post(
	'',
	response_model=BrowserAgentRunResponse,
	status_code=status.HTTP_201_CREATED,
)
def post_browser_agent_run(
	request: BrowserAgentRunCreateRequest,
	session: Annotated[Session, Depends(get_db_session)],
	current_user: Annotated[User, Depends(get_current_user)],
) -> BrowserAgentRunResponse:
	"""Queue a new browser-agent run for the current user."""
	try:
		response = queue_browser_agent_run(
			session,
			user=current_user,
			request=request,
		)
		session.commit()
		return response
	except BrowserAgentAdmissionError as exc:
		session.rollback()
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail=str(exc),
		) from exc
	except Exception:
		session.rollback()
		raise


@router.post(
	'/{run_id}/cancel',
	response_model=BrowserAgentCancelResponse,
	status_code=status.HTTP_200_OK,
)
def post_browser_agent_run_cancel(
	run_id: UUID,
	session: Annotated[Session, Depends(get_db_session)],
	current_user: Annotated[User, Depends(get_current_user)],
) -> BrowserAgentCancelResponse:
	"""Cancel a queued or running browser-agent run owned by the current user."""
	try:
		response = request_browser_agent_run_cancellation(
			session,
			user_id=current_user.id,
			run_id=run_id,
		)
		session.commit()
		return response
	except BrowserAgentRunNotFoundError as exc:
		session.rollback()
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
	except BrowserAgentRunAlreadyFinishedError as exc:
		session.rollback()
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
	except Exception:
		session.rollback()
		raise
