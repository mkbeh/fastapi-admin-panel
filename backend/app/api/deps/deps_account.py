from fastapi import Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

import errors
from models import Account
from extra.enums import Roles

from .deps_auth import get_user_id_from_token, db_session


async def get_current_user(
    db: AsyncSession = Depends(db_session),
    account_id: int = Depends(get_user_id_from_token),
) -> Account:
    return await select(Account).filter_by(id=account_id).scalar_one(db)


async def get_current_active_user(
    account: Account = Depends(get_current_user),
) -> Account:
    if not account.is_active:
        raise errors.InactiveAccount
    return account


async def get_current_active_superuser(
    account: Account = Depends(get_current_active_user),
) -> Account:
    if account.has_role(role=Roles.admin):
        return account
    raise errors.NotEnoughPrivileges
