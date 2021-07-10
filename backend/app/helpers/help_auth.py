from datetime import datetime

from sqlalchemy import not_
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import errors
import schemas

from models import AuthorizationData
from extra import enums

from core.security import verify_confirmation_code
from services.mailing import messages


async def authenticate_user(
    db: AsyncSession,
    params: schemas.LoginParams
) -> int:
    auth_data = await AuthorizationData\
        .with_joined('account')\
        .filter(
            AuthorizationData.login == params.login,
            not_(AuthorizationData.registration_type == enums.RegistrationTypes.social)
        ).scalar_one_or_none(db)

    if auth_data is None:
        raise errors.LoginError

    if not auth_data.is_confirmed:
        account = auth_data.account

        await messages.ConfirmAccountMessage(
            account_id=account.id,
            email=account.email
        ).send()

        raise errors.AccountIsNotConfirmed

    if not auth_data.verify_password(params.password):
        raise errors.LoginError

    return auth_data.account_id


async def confirm_account(
    db: AsyncSession,
    params: schemas.ConfirmAccountParams
) -> AuthorizationData:
    data = verify_confirmation_code(params.code, 'account_id')
    if not data:
        raise errors.BadConfirmationCode

    auth_data = await select(AuthorizationData)\
        .filter_by(account_id=data['account_id'])\
        .scalar_one_or_none(db)
    if not auth_data:
        raise errors.BadConfirmationCode
    if auth_data.confirmed_at:
        raise errors.BadConfirmationCode

    return await auth_data.update(db, confirmed_at=datetime.utcnow())


async def change_password(
    db: AsyncSession,
    params: schemas.ChangePasswordParams
) -> AuthorizationData:
    data = verify_confirmation_code(params.code, 'account_id')
    if not data:
        raise errors.BadConfirmationCode

    auth_data = await select(AuthorizationData).filter_by(
        account_id=data['account_id']
    ).scalar_one_or_none(db)
    if not auth_data:
        raise errors.BadConfirmationCode

    fields = dict(password=params.new_password)
    if not auth_data.confirmed_at:
        fields.update(confirmed_at=datetime.utcnow())
    return await auth_data.update(db, **fields)
