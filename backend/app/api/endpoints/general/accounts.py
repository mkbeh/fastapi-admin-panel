from typing import Any, List
from fastapi import APIRouter, Depends

import errors
import schemas

from models import Account, Role
from api.deps import deps_common, deps_account
from api.responses import with_errors


router = APIRouter()


@router.get('/me', response_model=schemas.Account)
async def get_me(
    account: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    return account


@router.get("/{object_id}", response_model=schemas.Account)
async def read_account_by_id(
    object_id: int,
    account: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Get a specific user by id"""
    pass


@router.get('/', response_model=schemas.ResultSchema)
async def read_accounts(
    commons: deps_common.CommonQueryParams = Depends(),
    account: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Retrieve accounts"""
    pass


@router.post(
    "/",
    response_model=schemas.Account,
    response_model_include={'id'},
    responses=with_errors(errors.AccountAlreadyExist),
)
async def create_account(
    *,
    schema_in: schemas.AccountCreate,
    account: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Create new account"""
    pass


@router.put(
    '/',
    response_model=schemas.Account,
    response_model_include={'id'}
)
async def update_account(
    *,
    object_id: int,
    schema_in: schemas.AccountUpdate,
    account: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Update current account"""
    pass


@router.delete('/', response_model=schemas.ResultResponse)
async def delete_object_by_id(
    object_id: int,
    current_account: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    pass
