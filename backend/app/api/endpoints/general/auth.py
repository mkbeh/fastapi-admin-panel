from typing import Any
from fastapi import (
    APIRouter, Depends, Body, status,
    Request,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

import errors
import models
import schemas

from core import security
from extra import enums
from helpers import help_auth
from services import socials

from api.deps import deps_auth, deps_account
from api.responses import with_errors


router = APIRouter()


@router.post(
    "/access-token",
    response_model=schemas.AuthToken,
    responses=with_errors(errors.LoginError)
)
async def access_token(
    params: schemas.LoginParams = Body(
        ...,
        example={
            "login": "admin@admin.com",
            "password": "admin123"
        },
    ),
    db: AsyncSession = Depends(deps_auth.db_session)
) -> Any:
    """
    OAuth2 compatible token login, get pair of access
    and refresh tokens for future requests.
    """
    account_id = await help_auth.authenticate_user(db, params=params)
    return security.generate_token(account_id)


@router.post(
    "/refresh-token",
    response_model=schemas.AuthToken,
    responses=with_errors(errors.BadToken, errors.TokenExpired)
)
async def refresh_token(
    account: models.Account = Depends(deps_auth.verify_refresh_token),
) -> Any:
    """Refresh access and refresh tokens pair via refresh token."""
    return security.generate_token(account.id)


@router.get(
    '/user_is_auth',
    responses=with_errors(errors.BadToken, errors.NotEnoughPrivileges)
)
async def user_is_auth(
    _: models.Account = Depends(deps_account.get_current_active_user)
) -> Any:
    """Token validation of active user."""
    return schemas.ResultResponse()


@router.get(
    '/social/{social_type}/url',
    responses={
        status.HTTP_307_TEMPORARY_REDIRECT: {
            'description': 'Redirect to social login or root'
        },
    },
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def get_social_login_url(
    request: Request,
    social_type: enums.SocialTypes
) -> Any:
    """Get a link for authorization in social networks."""
    try:
        await deps_account.get_current_active_user(request)
    except Exception:
        # first step in authorization
        url = socials.get_url_to_redirect(social_type)
    else:
        # already logged-in
        url = '/personal_area'

    return RedirectResponse(url)


@router.post(
    '/social/send_confirmation_email',
    response_model=schemas.ResultResponse,
    responses={
        status.HTTP_200_OK: {'description': 'Email was sent'},
        status.HTTP_400_BAD_REQUEST: {'description': 'Bad request'},
    }
)
async def social_login_send_confirmation_email(
    form: schemas.RequestConfirmationEmailBySocialCode = Body(
        ...,
        description='Code and email are required'
    ),
    db: AsyncSession = Depends(deps_auth.db_session),
) -> Any:
    """Email confirmation for social login, if the email was not provided."""
    await socials.send_confirmation_email(db, form)
    return schemas.ResultResponse()
