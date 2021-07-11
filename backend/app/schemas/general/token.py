from extra import enums
from schemas.base import BaseModel


class AuthToken(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = 'Bearer'


class AuthTokenPayload(BaseModel):
    sub: int
    purpose: enums.TokenPurpose


class RefreshTokenParams(BaseModel):
    refresh_token: str
