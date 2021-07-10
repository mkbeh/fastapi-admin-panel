from typing import Optional

from fastapi import Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import errors
import schemas
from extra import enums
from models import Account

from db.sessions import in_transaction
from core.security import decode_token


# auto_error=False
# because without token fastapi raises 403, but we need 401
http_bearer = HTTPBearer(auto_error=False)


async def db_session():
    async with in_transaction() as db:
        yield db


def get_user_id_from_token(
    token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> int:
    if not token:
        raise errors.BadToken
    token_payload = decode_token(
        token=token.credentials,
        purpose=enums.TokenPurpose.access
    )
    return token_payload.sub


async def verify_refresh_token(
    params: schemas.RefreshTokenParams = Body(...),
    db: AsyncSession = Depends(db_session),
) -> Account:
    token_payload = decode_token(
        token=params.refresh_token,
        purpose=enums.TokenPurpose.refresh
    )
    return await select(Account) \
        .filter_by(id=token_payload.sub) \
        .scalar_one(db)
