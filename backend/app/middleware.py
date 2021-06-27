from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import NoResultFound

from core import sentry
from core.settings import settings
from errors.common import AppException


async def orm_error_handler(request: Request, exc: NoResultFound):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={'code': 'DoesNotExist', 'detail': 'Object does not exist'}
    )


async def known_error(request: Request, exc: Exception):
    """To handle manually created errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'code': exc.__class__.__name__, 'detail': exc.__doc__}
    )


def build_middlewares():
    middlewares = []
    if settings.is_production:
        middlewares.append(
            Middleware(BaseHTTPMiddleware, dispatch=sentry.dispatcher)
        )
        frontends = [
            settings.SERVER_DOMAIN,
        ]
    else:
        frontends = [
            'http://localhost:3000',
        ]

    middlewares.append(
        Middleware(
            CORSMiddleware,
            allow_origins=frontends,
            # allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
    )
    return middlewares


__all__ = build_middlewares()

exception_handlers = {
    NoResultFound: orm_error_handler,
    AppException: known_error
}
