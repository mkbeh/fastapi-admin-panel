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
    responses=with_errors(
        errors.LoginError,
        errors.AccountIsNotConfirmed,
    )
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
    responses=with_errors(
        errors.BadToken,
        errors.NotEnoughPrivileges
    )
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


@router.get(
    '/social/{social_type}/bind',
    response_model=schemas.DataUrl,
    responses=with_errors(errors.SocilaAlreadyBound)
)
async def bind_social(
    social_type: enums.SocialTypes,
    account: models.Account = Depends(deps_account.get_current_active_user),
    social_net: models.SocialIntegration = Depends(deps_account.get_social),
) -> Any:
    """Bind social network."""
    if social_net:
        raise errors.SocilaAlreadyBound

    url = socials.get_url_to_redirect(
        social_type=social_type,
        social_action=enums.SocialActions.bind,
        account_id=account.id,
    )
    return schemas.DataUrl(url=url)


@router.get(
    '/social/{social_type}/unbind',
    response_model=schemas.ResultResponse,
    responses=with_errors(
        errors.SocialNotBound,
        errors.DeletePrimaryAccountDenied,
    )
)
async def unbind_social(
    social_net: models.SocialIntegration = Depends(deps_account.get_social),
    account: models.Account = Depends(deps_account.get_current_active_user),
    db: AsyncSession = Depends(deps_auth.db_session),
) -> Any:
    """Unbind social network."""
    if not social_net:
        raise errors.SocialNotBound

    has_form_auth = await models.AuthorizationData.exists(
        session=db,
        account_id=account.id,
        registration_type=enums.RegistrationTypes.forms,
    )

    if not has_form_auth:
        bind_socials_count = await models.AuthorizationData.where(
            account_id=account.id,
            registration_type=enums.RegistrationTypes.social,
        ).count(db)

        if bind_socials_count < 2:
            raise errors.DeletePrimaryAccountDenied

    auth = await models.AuthorizationData.where(social_data__id=social_net.id).first(db)
    await auth.delete()

    return schemas.ResultResponse()
