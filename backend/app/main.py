import logging

import uvicorn
from fastapi import FastAPI

import api
import middleware
import signals
from core import sentry
from core.config import settings


def run_app() -> FastAPI:
    logging.basicConfig(level=settings.LOGGING_LEVEL)
    fastapi_params = dict(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        on_startup=signals.startup_callbacks,
        on_shutdown=signals.shutdown_callbacks,
        exception_handlers=middleware.exception_handlers,
        middleware=middleware.__all__,
    )
    if settings.is_production:
        # hide docs
        app = FastAPI(**fastapi_params, docs_url=None, redoc_url=None)
    else:
        # hide docs behind password
        app = FastAPI(**fastapi_params, docs_url=None, redoc_url=None, debug=True)

    app.include_router(api.api_router)

    if not settings.is_production:
        from api.meta.docs_security import secure_docs
        secure_docs(
            app,
            admin_username=settings.DOCS_ADMIN_USERNAME,
            admin_password=settings.DOCS_ADMIN_PASSWORD,
            **fastapi_params
        )

    if settings.is_production and settings.SENTRY_DSN:
        sentry.init(app)

    return app


if __name__ == "__main__":
    is_dev = settings.ENV == settings.EnvMode.dev
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        debug=is_dev,
        reload=is_dev,
        reload_dirs=is_dev and ['backend/app'] or None,
        log_level=settings.LOGGING_LEVEL.lower(),
    )
else:
    app = run_app()
