import errors
import schemas

from sqlalchemy import not_
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Account, AuthorizationData
from extra import enums


async def authenticate_user(
    db: AsyncSession,
    params: schemas.LoginParams
) -> int:
    auth_data = (
        await select(AuthorizationData)
        .filter(
            AuthorizationData.login == params.login,
            not_(AuthorizationData.registration_type == enums.RegistrationTypes.social)
        )
        .join(AuthorizationData.account)
        .options(joinedload(AuthorizationData.account))
        .unique(db)
    ).scalar_one_or_none()

    if auth_data is None:
        raise errors.LoginError

    if not auth_data.is_confirmed:
        account = auth_data.account

        # TODO: send confirmation email

        raise errors.AccountIsNotConfirmed

    if not auth_data.verify_password(params.password):
        raise errors.LoginError

    return auth_data.account_id
