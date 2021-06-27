from typing import Optional

from fastapi import Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import errors
import schemas
from extra import enums
from models import Account
from core.security import decode_token


# auto_error=False
# because without token fastapi raises 403, but we need 401
http_bearer = HTTPBearer(auto_error=False)


async def get_account_id_from_token(
    token: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> int:
    """ Получение токена из заголовков или cookie """
    if not token:
        raise errors.BadToken
    token_payload = decode_token(token.credentials, purpose=enums.TokenPurpose.access)
    return token_payload.sub


async def verify_refresh_token(
    params: schemas.RefreshTokenParams = Body(...),
) -> Account:
    token_payload = decode_token(params.refresh_token, purpose=enums.TokenPurpose.refresh)
    return await Account.select('id').filter_by(id=token_payload.sub).one()
