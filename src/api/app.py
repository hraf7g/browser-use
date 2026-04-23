from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.ai.factory import build_ai_runtime
from src.api.routes.activity import router as activity_router
from src.api.routes.auth import router as auth_router
from src.api.routes.browser_agent_runs import router as browser_agent_runs_router
from src.api.routes.health import router as health_router
from src.api.routes.keyword_profile import router as keyword_profile_router
from src.api.routes.me import router as me_router
from src.api.routes.notification_settings import router as notification_settings_router
from src.api.routes.operator_status import router as operator_status_router
from src.api.routes.tenders import router as tenders_router
from src.shared.config.settings import get_settings
from src.shared.logging.logger import get_logger, setup_logging


def create_app() -> FastAPI:
	"""Create and configure the FastAPI application."""
	settings = get_settings()
	ai_runtime = build_ai_runtime(settings)
	setup_logging(settings)
	logger = get_logger(__name__)

	@asynccontextmanager
	async def lifespan(app: FastAPI):
		logger.info(
			'runtime_cookie_config '
			f'cookie_name={settings.auth_cookie_name} '
			f'same_site={settings.auth_cookie_same_site} '
			f'secure={settings.auth_cookie_secure or settings.environment == "production"} '
			f'path={settings.auth_cookie_path} '
			f'domain={settings.auth_cookie_domain!r}'
		)
		logger.info(
			'runtime_frontend_config '
			f'frontend_base_url={settings.frontend_base_url} '
			f'frontend_origin={settings.frontend_origin} '
			f'cors_origins={",".join(settings.cors_allow_origins_list)}'
		)
		logger.info(
			'runtime_ai_config '
			f'ai_provider={ai_runtime.provider} '
			f'ai_model={settings.ai_model!r} '
			f'ai_fallback_model={settings.ai_fallback_model!r} '
			f'ai_bedrock_use_ambient_credentials={settings.ai_bedrock_use_ambient_credentials}'
		)
		logger.info(
			'application_startup',
			extra={
				'app_name': settings.app_name,
				'environment': settings.environment,
			},
		)
		yield
		logger.info('application_shutdown')

	app = FastAPI(
		title=settings.app_name,
		debug=settings.debug,
		lifespan=lifespan,
	)

	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.cors_allow_origins_list,
		allow_credentials=True,
		allow_methods=['*'],
		allow_headers=['*'],
	)

	app.include_router(health_router)
	app.include_router(auth_router)
	app.include_router(browser_agent_runs_router)
	app.include_router(me_router)
	app.include_router(activity_router)
	app.include_router(keyword_profile_router)
	app.include_router(notification_settings_router)
	app.include_router(tenders_router)
	app.include_router(operator_status_router)

	return app


app = create_app()
