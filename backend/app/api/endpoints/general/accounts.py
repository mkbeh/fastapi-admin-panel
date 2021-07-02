from fastapi import APIRouter, Depends

from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

import errors
import schemas

from models import Account, AuthorizationData
from utils import decorators
from helpers import help_account

from extra import enums
from services.mailing import messages

from api.deps import deps_common, deps_account, deps_auth
from api.responses import with_errors


router = APIRouter()


@router.get(
    "/me",
    response_model=schemas.Account
)
async def get_me(
    account: Account = Depends(deps_account.get_current_active_superuser),
):
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
):
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
):
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
):
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
):
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
):
    await delete(Account).filter_by(id=object_id).execute(db)
    return schemas.ResultResponse()


@router.post(
    '/registration',
    response_model=schemas.ResultResponse,
    responses=with_errors(errors.AccountAlreadyExist),
)
async def account_registration(
    schema_in: schemas.AccountCreateOpen,
    db: AsyncSession = Depends(deps_auth.db_session),
):
    """Account registration through the form using email"""
    if await help_account.is_email_exists(db, email=schema_in.email):
        raise errors.AccountAlreadyExist

    account = await Account.create(
        db=db,
        email=schema_in.email,
        password=schema_in.password,
    )

    await messages.ConfirmAccountMessage(
        account_id=account.id,
        email=schema_in.email,
    ).send()

    return schemas.ResultResponse()


@router.post(
    '/change_password',
    response_model=schemas.ResultResponse,
    responses=with_errors(errors.EmailIsNotFound)
)
async def change_account_password(
    schema_in: schemas.SendEmailChangePassword,
    db: AsyncSession = Depends(deps_auth.db_session)
):
    """Send email to change account password"""
    auth_data = await select(AuthorizationData).filter_by(
        login=schema_in.login,
        registration_type=enums.RegistrationTypes.forms,
    ).scalar_one_or_none(db)

    if not auth_data:
        # no email found
        raise errors.EmailIsNotFound

    await messages.ChangePasswordMessage(
        account_id=auth_data.account_id,
        email=schema_in.login
    ).send()

    return schemas.ResultResponse()
