from typing import Optional, Any
from fastapi import APIRouter, status, Depends, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

import schemas
import errors

from helpers import help_auth

from services import socials
from services.mailing import messages

from extra.enums import SocialTypes
from core.security import generate_token

from api.deps import deps_auth
from api.responses import with_errors


router = APIRouter()


@router.post(
    '/confirm/account',
    response_model=schemas.AuthToken,
    responses=with_errors(errors.BadConfirmationCode),
)
async def confirm_account(
    params: schemas.ConfirmAccountParams = Body(...),
    db: AsyncSession = Depends(deps_auth.db_session)
) -> Any:
    """Confirms the account, logs in the user and returns the token"""
    auth_data = await help_auth.confirm_account(db, params)
    await messages.SuccessfulRegistrationMessage(email=auth_data.login).send()
    return generate_token(auth_data.account_id)


@router.post(
    '/change_password',
    response_model=schemas.ResultResponse,
    responses=with_errors(errors.BadConfirmationCode)
)
async def change_password(
    params: schemas.ChangePasswordParams,
    db: AsyncSession = Depends(deps_auth.db_session)
) -> Any:
    """Account password recovery"""
    auth_data = await help_auth.change_password(db, params)
    await messages.PasswordWasChangedMessage(
        email=auth_data.login
    ).send()
    return schemas.ResultResponse()


@router.get(
    '/social/{social_type}',
    responses={
        status.HTTP_307_TEMPORARY_REDIRECT: {
            'description': 'Redirect to frontend connect page'
        },
        status.HTTP_400_BAD_REQUEST: {
            'description': 'Bad request params'
        }
    },
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
)
async def social_login(
    social_type: SocialTypes,
    code: str,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: AsyncSession = Depends(deps_auth.db_session)
) -> Any:
    """Autorization via OAUTH service"""
    if error and error_description:
        return RedirectResponse(
            f'/connect/error?error={error}&error_description={error_description}'
        )

    schema = await socials.get_user_schema(social_type, code)
    if not schema.email:
        # user doesn't have an email in social profile
        return RedirectResponse(f'/connect/mail?code={code}')

    # user registration
    await socials.registration(db, schema, code)

    return RedirectResponse(f'/connect?code={code}')
