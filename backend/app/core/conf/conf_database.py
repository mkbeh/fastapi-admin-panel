from typing import Optional, Dict, Any

import aioredis
from aiocache import Cache
from aiocache.serializers import MsgPackSerializer

from pydantic import (
    BaseSettings,
    PostgresDsn,
    validator,
    RedisDsn,
)
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
        pre=True,
    )
    def assemble_postgres_connection(
        cls, val: Optional[str], values: Dict[str, Any], field: ModelField
    ) -> Any:
        if isinstance(val, str):
            return val
        if field.name == "SQLALCHEMY_DATABASE_URI":
            pwd = values.get("POSTGRES_PASSWORD")
        if field.name == "SQLALCHEMY_DATABASE_URI_HIDDEN_PWD":
            pwd = "*" * 4
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=values.get("POSTGRES_USER"),
            password=pwd,
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
            port=values.get("POSTGRES_PORT"),
        )


class RedisSettings(BaseSettings):
    """Настройки редиса"""

    REDIS_HOST: Optional[str] = "localhost"
    REDIS_PORT: Optional[str] = "6379"
    REDIS_DB: Optional[str] = "0"
    REDIS_URI: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = "foobared"

    @validator("REDIS_URI", pre=True)
    def assemble_redis_connection(
        cls, val: Optional[str], values: Dict[str, Any]
    ) -> str:
        """получение URL для редиса"""
        if isinstance(val, str):
            return val

        return RedisDsn.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
            path=f"/{values.get('REDIS_DB') or ''}",
        )

    # default 20 minutes
    DEFAULT_CACHE_TTL = 20 * 60
    DEFAULT_CACHE_PARAMS: Optional[Dict] = None

    @validator("DEFAULT_CACHE_PARAMS", pre=True)
    def assemble_cache_params(
        cls, val: Optional[str], values: Dict[str, Any]
    ) -> Dict:
        return dict(
            cache=Cache.REDIS,
            serializer=MsgPackSerializer(encoding=None, use_list=True),
            endpoint=values["REDIS_HOST"],
            port=values["REDIS_PORT"],
            password=values["REDIS_PASSWORD"],
        )

    REDIS_POOL: aioredis.commands.Redis = None
