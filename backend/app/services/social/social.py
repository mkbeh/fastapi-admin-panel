from typing import Union

import httpx
from pydantic import ValidationError
from aiogoogle import AiogoogleError

from sqlalchemy.ext.asyncio import AsyncSession

import errors
import schemas

from extra import enums
from models import Account, SocialIntegration, AuthorizationData
from sessions import sessions

from utils.misc import get_random_string, create_secret as create_state
from helpers.help_account import is_email_exists

from core.settings import settings
from core.security import generate_token

from services.mailing import messages


def get_url_to_redirect(social_type: enums.SocialTypes):
    """Getting a link for OAuth authorization"""
    # first step in authorization - url to redirect user browser
    if social_type == enums.SocialTypes.vk:
        url = f'https://oauth.vk.com/authorize?client_id={settings.OAUTH_VK_CLIENT_ID}'\
              f'&redirect_uri={settings.OAUTH_VK_REDIRECT_URI}'\
              f'&scope=email&response_type=code&display=popup&v=5.124'

    elif social_type == enums.SocialTypes.facebook:
        url = f'https://www.facebook.com/v8.0/dialog/oauth?'\
              f'client_id={settings.OAUTH_FB_CLIENT_ID}'\
              f'&redirect_uri={settings.OAUTH_FB_REDIRECT_URI}'\
              f'&scope=email&response_type=code'\
              f'&state={create_state()}'

    elif social_type == enums.SocialTypes.google:
        url = sessions.google_session.openid_connect.authorization_url(
            state=create_state(),
            nonce=create_state(),
            include_granted_scopes=True,
        )

    return url


async def get_facebook_user(code: str):
    """Getting user id and email from facebook API"""
    session = sessions.facebook_session
    params = dict(
        code=code,
        client_id=settings.OAUTH_FB_CLIENT_ID,
        client_secret=settings.OAUTH_FB_CLIENT_SECRET,
        redirect_uri=settings.OAUTH_FB_REDIRECT_URI,
    )
    text = None
    try:
        # getting token
        async with session.get(
            'https://graph.facebook.com/v8.0/oauth/access_token',
            params=params
        ) as resp:
            if resp.status != 200:
                raise errors.SocialLoginFailed
            text = await resp.text()

        req = schemas.FacebookAccessTokenRequest.parse_raw(text)
        params = dict(
            fields='id,name,email',
            access_token=req.access_token,
        )
        # getting user fields
        async with session.get('https://graph.facebook.com/me', params=params) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise errors.SocialLoginFailed

        schema = schemas.RegistrationFromSocialFacebook.parse_raw(text)

    except (httpx.RequestError, ValidationError):
        # if exception was raised by httpx or pydantic
        if text:
            # so one response was successful
            try:
                req = schemas.GetFacebookAccessTokenBadRequest.parse_raw(text)
            except ValidationError:
                ...
            else:
                raise errors.SocialLoginFailed(req.error_description)
        raise errors.SocialLoginFailed

    return schema


async def get_vk_user(code: str):
    """Getting user id and email from VK API"""
    session = sessions.vk_session
    params = dict(
        code=code,
        client_id=settings.OAUTH_VK_CLIENT_ID,
        client_secret=settings.OAUTH_VK_CLIENT_SECRET,
        redirect_uri=settings.OAUTH_VK_REDIRECT_URI,
    )
    text = None
    try:
        # getting token and email at once
        async with session.get('https://oauth.vk.com/access_token', params=params) as resp:
            if resp.status != 200:
                raise errors.SocialLoginFailed
            text = await resp.text()

        schema = schemas.RegistrationFromSocialVK.parse_raw(text)

    except (httpx.RequestError, ValidationError):
        # if exception was raised by httpx or pydantic
        if text:
            # so one response was succesful
            try:
                req = schemas.GetVKAccessTokenBadRequest.parse_raw(text)
            except ValidationError:
                ...
            else:
                raise errors.SocialLoginFailed(req.error_description)
        raise errors.SocialLoginFailed

    return schema


async def get_google_user(code: str, state=None):
    """Getting user id and email from Google API"""
    session = sessions.google_session
    try:
        # getting token
        user_creds = await session.openid_connect.build_user_creds(
            grant=code,
        )
        # getting user fields
        user_info = await session.openid_connect.get_user_info(user_creds)
        schema = schemas.RegistrationFromSocialGoogle.parse_obj(user_info)
    except (httpx.RequestError, ValidationError, AiogoogleError):
        raise errors.SocialLoginFailed

    return schema


__social_user_cache = {}


async def get_user_schema(social_type: enums.SocialTypes, code: str):
    """Retrieving User Data by OAuth Code"""

    if code not in __social_user_cache:
        schema = None

        if social_type == enums.SocialTypes.vk:
            schema = await get_vk_user(code)

        if social_type == enums.SocialTypes.facebook:
            schema = await get_facebook_user(code)

        if social_type == enums.SocialTypes.google:
            schema = await get_google_user(code)

        if schema is None:
            raise errors.UnknownSocialType

        __social_user_cache[code] = schema

    return __social_user_cache[code]


def get_token(code: str):
    """Issuing an authorization token for an account bound by OAuth authorization"""
    if user_schema := __social_user_cache.get(code):
        # user was redirected from social login right now
        if not user_schema.email or not user_schema.application_account_id:
            # sanity check
            # confused endpoint, something is wrong with the frontend
            raise errors.SocialUserEmailIsNotConfirmed
        __social_user_cache.pop(code)
        return generate_token(user_schema.application_account_id)
    else:
        raise errors.BadSocialCode


async def send_confirmation_email(
    db: AsyncSession,
    form: schemas.RequestConfirmationEmailBySocialCode
):
    if schema := __social_user_cache.get(form.code):
        # user was redirected from social login right now
        if await is_email_exists(db, form.email):
            # sorry, email is registered
            raise errors.EmailIsExists

        schema.email = form.email
        # creating account
        social_type, external_id = schema.get_type_and_user_id()

        account = await Account.create(
            db=db,
            email=schema.email,
            password=get_random_string(),
            registration_type=enums.RegistrationTypes.social,
            social_type=social_type,
            external_id=external_id
        )

        await messages.ConfirmAccountMessage(
            account_id=account.id,
            email=schema.email
        ).send()

    else:
        raise errors.BadSocialCode


async def registration(
    db: AsyncSession,
    schema: Union[
        schemas.RegistrationFromSocialVK,
        schemas.RegistrationFromSocialFacebook,
        schemas.RegistrationFromSocialGoogle,
    ],
    code: str,
):
    social_type, external_id = schema.get_type_and_user_id()

    social_integration = await SocialIntegration.where(
        social_type=social_type,
        external_id=external_id,
    ).scalar_one_or_none(db)

    if social_integration:
        # user was logged in before through this social
        auth_data = await social_integration.auth_data
        account_id = auth_data.account_id
    else:
        auth_data = await AuthorizationData.where(
            login=schema.email,
            registration_type=enums.RegistrationTypes.social,
        ).scalar_one_or_none(db)
        if auth_data:
            # user was logged in before through another social with this email
            await SocialIntegration.create(
                db=db,
                auth_data_id=auth_data.id,
                social_type=social_type,
                external_id=external_id
            )
            account_id = auth_data.account_id
        else:
            account = await Account.where(
                email=schema.email
            ).scalar_one_or_none(db)
            if account:
                auth_data = await AuthorizationData.create(
                    db=db,
                    account_id=account.id,
                    registration_type=enums.RegistrationTypes.social,
                    login=schema.email,
                    password=get_random_string()
                )
                await SocialIntegration.create(
                    db=db,
                    auth_data_id=auth_data.id,
                    social_type=social_type,
                    external_id=external_id
                )
            else:
                # totally new user
                account = await Account.create(
                    db=db,
                    email=schema.email,
                    password=get_random_string(),
                    registration_type=enums.RegistrationTypes.social,
                    social_type=social_type,
                    external_id=external_id
                )

                await messages.ConfirmAccountMessage(
                    account_id=account.id,
                    email=schema.email
                ).send()

            account_id = account.id

    # store account_id for next frontend retrieval
    __social_user_cache[code].application_account_id = account_id
