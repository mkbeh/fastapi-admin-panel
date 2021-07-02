import secrets
from pydantic import BaseSettings


class AuthSettings(BaseSettings):
    AUTH_SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 1 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1
    # 60 minutes * 24 hours * 8 days = 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    # 60 minutes
    EMAIL_CODE_EXPIRE_MINUTES: int = 60 * 60

    OAUTH_VK_CLIENT_ID: str
    OAUTH_VK_CLIENT_SECRET: str
    OAUTH_VK_REDIRECT_URI: str

    OAUTH_FB_CLIENT_ID: str
    OAUTH_FB_CLIENT_SECRET: str
    OAUTH_FB_REDIRECT_URI: str

    OAUTH_GOOGLE_CLIENT_ID: str
    OAUTH_GOOGLE_CLIENT_SECRET: str
    OAUTH_GOOGLE_REDIRECT_URI: str
