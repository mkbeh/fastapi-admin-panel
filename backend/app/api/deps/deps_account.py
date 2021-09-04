from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

import errors
import schemas
from extra import enums
from models import Account, SocialIntegration
from extra.enums import Roles

from .deps_auth import get_user_id_from_token, db_session


async def get_current_user(
    db: AsyncSession = Depends(db_session),
    account_id: int = Depends(get_user_id_from_token),
) -> Account:
    account = await Account.where(id=account_id).one_or_none(db)
    if not account:
        raise errors.AccountNotFound
    return account


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


async def get_social(
    social_type: enums.SocialTypes,
    account: Account = Depends(get_current_active_user),
    db: AsyncSession = Depends(db_session),
) -> Optional[SocialIntegration]:
    return await SocialIntegration.where(
        social_type=social_type,
        auth_data___account___id=account.id,
        auth_data___registration_type=enums.RegistrationTypes.social,
    ).one_or_none(db)


def get_social_state(state: str) -> schemas.SocialState:
    return schemas.SocialState.parse_raw(state)
