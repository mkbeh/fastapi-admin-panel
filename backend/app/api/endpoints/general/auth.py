from typing import Any

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

import errors
import models
import schemas

from core import security
from helpers import help_login
from api.deps import deps_auth
from api.responses import with_errors


router = APIRouter()


@router.post(
    "/access-token",
    response_model=schemas.AuthToken,
    responses=with_errors(errors.LoginError)
)
async def access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get pair of access
    and refresh tokens for future requests.
    """
    account_id = await help_login.authenticate(
        email=form_data.username,
        password=form_data.password,
    )
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
