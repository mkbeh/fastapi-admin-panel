from extra import enums
from schemas.base import ConfiguredBaseModel


class AuthToken(ConfiguredBaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = 'Bearer'


class AuthTokenPayload(ConfiguredBaseModel):
    sub: int
    purpose: enums.TokenPurpose


class RefreshTokenParams(ConfiguredBaseModel):
    refresh_token: str

