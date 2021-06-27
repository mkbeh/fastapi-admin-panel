""" Sentry middlewares """

from fastapi import HTTPException
from starlette.responses import Response
from starlette.requests import Request
from starlette.middleware.base import RequestResponseEndpoint

import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from api.deps import deps_auth
from core.settings import settings


def init(app):
    """
    Инициализация сервиса sentry.
    подробнее: https://sentry.io/
    """
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        # Sample rate - частота отправки ошибок в %. Максимальное значение 1.0.
        # Если одна и таrже ошибка будет повторяться, тогда sentry будет отправлять только каждую четвертую ошибку.
        # Документацией рекомендуется начинать с значения 0.25 и увеличивать при необходимости.
        sample_rate=0.25,
        integrations=[
            SqlalchemyIntegration(),  # Интеграция SQLAlchemy фиксирует запросы в БД в виде хлебных крошек.
            AioHttpIntegration(),
        ],
    )
    SentryAsgiMiddleware(app=app)


async def send_data(request, exception) -> None:
    """Конфигурирует и отправляет данные об ошибках и исключениях в sentry."""
    try:
        account_id = await deps_auth.get_account_id_from_token(request)
    except HTTPException:
        return

    with sentry_sdk.push_scope() as scope:
        scope.set_context("request", request)
        scope.user = {
            "ip_address": request.client.host,
            "id": account_id,
        }
        sentry_sdk.capture_exception(exception)


async def dispatcher(request: Request, call_next: RequestResponseEndpoint) -> Response:
    try:
        return await call_next(request)
    except Exception as exc:
        await send_data(request, exc)
        raise
