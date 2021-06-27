from typing import Optional, Dict, Any
from pydantic import BaseSettings, PostgresDsn, validator
from pydantic.fields import ModelField


class DatabaseSettings(BaseSettings):
    POSTGRES_SERVER: Optional[str]
    POSTGRES_USER: Optional[str]
    POSTGRES_PASSWORD: Optional[str]
    POSTGRES_DB: Optional[str]
    POSTGRES_PORT: Optional[str]
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    SQLALCHEMY_DATABASE_URI_HIDDEN_PWD: Optional[str] = None

    @validator(
        "SQLALCHEMY_DATABASE_URI",
        "SQLALCHEMY_DATABASE_URI_HIDDEN_PWD",
        pre=True
    )
    def assemble_postgres_connection(
            cls,
            val: Optional[str],
            values: Dict[str, Any],
            field: ModelField
    ) -> Any:
        if isinstance(val, str):
            return val
        if field.name == 'SQLALCHEMY_DATABASE_URI':
            pwd = values.get("POSTGRES_PASSWORD")
        if field.name == 'SQLALCHEMY_DATABASE_URI_HIDDEN_PWD':
            pwd = '*' * 4
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=pwd,
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
            port=values.get("POSTGRES_PORT")
        )
