from fastapi import Depends

import errors
from extra import enums
from models import Account, Role

from .deps_auth import get_account_id_from_token


async def get_current_account(
    account_id: int = Depends(get_account_id_from_token),
) -> Account:
    # TODO: get account
    return


async def get_current_active_account(
    account: Account = Depends(get_current_account),
) -> Account:
    if not account.is_active:
        raise errors.InactiveAccount
    return account


async def get_current_active_superuser(
    account: Account = Depends(get_current_active_account),
) -> Account:
    if account.role.name == enums.Roles.admin:
        return account
    raise errors.NotEnoughPrivileges
