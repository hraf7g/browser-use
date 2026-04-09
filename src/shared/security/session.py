from __future__ import annotations

from fastapi import Request, Response

from src.shared.config.settings import get_settings


def get_access_token_from_cookie(request: Request) -> str | None:
	"""Return the normalized auth cookie token if one is present."""
	token = request.cookies.get(get_settings().auth_cookie_name)
	if token is None:
		return None

	normalized = token.strip()
	return normalized or None


def set_access_token_cookie(response: Response, token: str) -> None:
	"""Persist an access token in a hardened httpOnly cookie."""
	settings = get_settings()
	max_age_seconds = settings.auth_access_token_ttl_minutes * 60
	response.set_cookie(
		key=settings.auth_cookie_name,
		value=token,
		max_age=max_age_seconds,
		expires=max_age_seconds,
		path=settings.auth_cookie_path,
		domain=settings.auth_cookie_domain,
		secure=settings.auth_cookie_secure or settings.environment == 'production',
		httponly=True,
		samesite=settings.auth_cookie_same_site,
	)


def clear_access_token_cookie(response: Response) -> None:
	"""Delete the auth cookie using the same attributes used to set it."""
	settings = get_settings()
	response.delete_cookie(
		key=settings.auth_cookie_name,
		path=settings.auth_cookie_path,
		domain=settings.auth_cookie_domain,
		secure=settings.auth_cookie_secure or settings.environment == 'production',
		httponly=True,
		samesite=settings.auth_cookie_same_site,
	)
