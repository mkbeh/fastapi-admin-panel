from typing import Any
from fastapi import APIRouter, Depends

from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

import errors
import schemas

from models import Account
from utils import decorators
from helpers import help_account
from api.deps import deps_common, deps_account, deps_auth
from api.responses import with_errors


router = APIRouter()


@router.get(
    "/me",
    response_model=schemas.Account
)
async def get_me(
    account: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Get a current user"""
    return account


@router.get(
    "/{object_id}",
    response_model=schemas.Account
)
async def read_account_by_id(
    object_id: int,
    db: AsyncSession = Depends(deps_auth.db_session),
    _: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Get a specific user by id"""
    return await select(Account).filter_by(id=object_id).scalar_one(db)


@router.get(
    "/",
    response_model=schemas.ResultSchema
)
@decorators.add_count(Account)
async def read_accounts(
    commons: deps_common.CommonQueryParams = Depends(),
    db: AsyncSession = Depends(deps_auth.db_session),
    _: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Retrieve accounts"""
    accounts = await select(Account) \
        .offset(commons.skip) \
        .limit(commons.limit) \
        .scalars_all(db)

    return accounts, db


@router.post(
    "/",
    response_model=schemas.AccountInDB,
    responses=with_errors(errors.AccountAlreadyExist),
)
async def create_account(
    *,
    schema_in: schemas.AccountCreate,
    db: AsyncSession = Depends(deps_auth.db_session),
    _: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Create new account"""
    if await help_account.is_email_exists(db, email=schema_in.email):
        raise errors.AccountAlreadyExist
    return await Account.create(
        db=db,
        skip_confirmation=True,
        **schema_in.dict(exclude={'password2'})
    )


@router.put(
    "/",
    response_model=schemas.AccountInDB,
)
async def update_account(
    *,
    object_id: int,
    schema_in: schemas.AccountUpdate,
    db: AsyncSession = Depends(deps_auth.db_session),
    _: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    """Update current account"""
    db_obj = await select(Account) \
        .filter_by(id=object_id) \
        .scalar_one(db)

    return await db_obj.update(db, **schema_in.dict(exclude_unset=True))


@router.delete(
    "/",
    response_model=schemas.ResultResponse
)
async def delete_object_by_id(
    object_id: int,
    db: AsyncSession = Depends(deps_auth.db_session),
    _: Account = Depends(deps_account.get_current_active_superuser),
) -> Any:
    await delete(Account).filter_by(id=object_id).execute(db)
    return schemas.ResultResponse()
