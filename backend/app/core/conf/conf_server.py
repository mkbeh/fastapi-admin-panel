import enum
from typing import Dict, Any, Optional
from pydantic import BaseSettings, EmailStr, validator


class ServerSettings(BaseSettings):
    PROJECT_NAME: str = 'FastAPI-admin-panel'
    VERSION: str = '0.1.0'
    API_V1_STR: str = ''

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

    API_URL: Optional[str] = None

    @validator('API_URL')
    def validate_api_url(cls, value: str, values: Dict[str, Any]) -> str:
        return f'{values["SERVER_DOMAIN"]}/{values["API_V1_STR"].rstrip("/")}'

    SENTRY_DSN: Optional[str] = None

    FIRST_SUPERUSER_LOGIN: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    DOCS_ADMIN_USERNAME: str = 'admin'
    DOCS_ADMIN_PASSWORD: str = 'admin'
