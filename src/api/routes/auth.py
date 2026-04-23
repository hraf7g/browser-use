from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user_optional
from src.api.services.auth_service import (
	EmailAlreadyExistsError,
	InactiveUserError,
	InvalidCredentialsError,
	authenticate_user,
	build_user_summary,
	register_user,
)
from src.api.services.password_reset_service import (
	InvalidPasswordResetTokenError,
	request_password_reset,
	reset_password,
)
from src.db.models.user import User
from src.db.session import get_db_session
from src.email.password_reset_email_service import dispatch_password_reset_email
from src.shared.config.settings import get_settings
from src.shared.logging.logger import get_logger
from src.shared.schemas.auth import (
	ForgotPasswordRequest,
	ForgotPasswordResponse,
	LoginRequest,
	ResetPasswordRequest,
	ResetPasswordResponse,
	SessionStatusResponse,
	SignupRequest,
	UserSummary,
)
from src.shared.security.session import clear_access_token_cookie, set_access_token_cookie
from src.shared.security.tokens import create_access_token

router = APIRouter(prefix='/auth', tags=['auth'])
logger = get_logger(__name__)


@router.get(
	'/session',
	response_model=SessionStatusResponse,
	status_code=status.HTTP_200_OK,
)
def get_session_status(
	current_user: Annotated[User | None, Depends(get_current_user_optional)],
) -> SessionStatusResponse:
	"""Return the current auth session state without treating logout as an error."""
	if current_user is None:
		return SessionStatusResponse(authenticated=False, user=None)

	return SessionStatusResponse(
		authenticated=True,
		user=build_user_summary(current_user),
	)


@router.post(
	'/forgot-password',
	response_model=ForgotPasswordResponse,
	status_code=status.HTTP_202_ACCEPTED,
)
def forgot_password(
	payload: ForgotPasswordRequest,
	session: Annotated[Session, Depends(get_db_session)],
) -> ForgotPasswordResponse:
	"""Initiate the password reset flow without disclosing account existence."""
	try:
		result = request_password_reset(
			session=session,
			payload=payload,
		)
		session.commit()
		if result.delivered and result.recipient_email and result.reset_token:
			try:
				dispatch_password_reset_email(
					recipient_email=result.recipient_email,
					reset_token=result.reset_token,
					frontend_base_url=get_settings().frontend_base_url,
				)
			except Exception:
				logger.exception(
					'password_reset_email_dispatch_failed recipient_email=%s',
					result.recipient_email,
				)
		return ForgotPasswordResponse(
			accepted=True,
			message='If an account exists for this email, a password reset link will be delivered shortly.',
			delivery_channel=result.delivery_channel,
		)
	except Exception:
		session.rollback()
		raise


@router.post(
	'/reset-password',
	response_model=ResetPasswordResponse,
	status_code=status.HTTP_200_OK,
)
def reset_password_route(
	payload: ResetPasswordRequest,
	session: Annotated[Session, Depends(get_db_session)],
) -> ResetPasswordResponse:
	"""Reset the current password using a valid one-time reset token."""
	try:
		reset_password(
			session=session,
			payload=payload,
		)
		session.commit()
		return ResetPasswordResponse(
			message='Password updated successfully.',
		)
	except InvalidPasswordResetTokenError as exc:
		session.rollback()
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		) from exc
	except Exception:
		session.rollback()
		raise


@router.post(
	'/signup',
	response_model=UserSummary,
	status_code=status.HTTP_201_CREATED,
)
def signup(
	payload: SignupRequest,
	response: Response,
	session: Annotated[Session, Depends(get_db_session)],
) -> UserSummary:
	"""Register a new user account."""
	try:
		user = register_user(session=session, payload=payload)
		access_token = create_access_token(user_id=user.id, email=user.email)
		set_access_token_cookie(response, access_token)
		session.commit()
		return build_user_summary(user)
	except EmailAlreadyExistsError as exc:
		session.rollback()
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail=str(exc),
		) from exc
	except Exception:
		session.rollback()
		raise


@router.post(
	'/login',
	response_model=UserSummary,
	status_code=status.HTTP_200_OK,
)
def login(
	payload: LoginRequest,
	response: Response,
	session: Annotated[Session, Depends(get_db_session)],
) -> UserSummary:
	"""Authenticate a user and set the session cookie."""
	try:
		user, access_token = authenticate_user(session=session, payload=payload)
		session.commit()
		session.refresh(user)
		set_access_token_cookie(response, access_token)
		return build_user_summary(user)
	except (InvalidCredentialsError, InactiveUserError) as exc:
		session.rollback()
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=str(exc),
			headers={'WWW-Authenticate': 'Bearer'},
		) from exc
	except Exception:
		session.rollback()
		raise


@router.post(
	'/logout',
	status_code=status.HTTP_204_NO_CONTENT,
)
def logout(response: Response) -> None:
	"""Clear the current auth session cookie."""
	clear_access_token_cookie(response)
