import enum
import secrets
from typing import Dict, Any
from pydantic import BaseSettings, EmailStr, validator


class ServerSettings(BaseSettings):
    PROJECT_NAME: str = 'FastAPI-admin-panel'
    VERSION: str = '0.1.0'

    class EnvMode(enum.Enum):
        dev = 'DEV'
        prod = 'PROD'

    ENV: EnvMode = EnvMode.prod

    @property
    def is_production(self):
        return self.ENV == self.EnvMode.prod

    LOGGING_LEVEL: str = 'INFO'

    SERVER_HOST: str = '127.0.0.1'
    SERVER_PORT: int = 8000
    SERVER_DOMAIN: str = 'http://localhost'

    @validator('SERVER_DOMAIN')
    def validate_domain(cls, value: str, values: Dict[str, Any]) -> str:
        return value.rstrip('/')

    API_V1_STR: str = ''

    AUTH_SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 1 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1
    # 60 minutes * 24 hours * 8 days = 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    # 60 minutes
    EMAIL_CODE_EXPIRE_MINUTES: int = 60 * 60

    SENTRY_DSN: str = None

    FIRST_SUPERUSER_LOGIN: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    DOCS_ADMIN_USERNAME: str = 'admin'
    DOCS_ADMIN_PASSWORD: str = 'admin'
