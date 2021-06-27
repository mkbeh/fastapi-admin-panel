import logging
from typing import Optional

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from tenacity import (
    after_log, before_log, retry,
    stop_after_attempt, wait_fixed,
)

from core.config import settings
from .model import Model


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('database')

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1

engine: Optional[AsyncEngine] = None
async_session: Optional[sessionmaker] = None

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def db_init() -> None:
    global engine, async_session

    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
    )

    Model.metadata.naming_convention = convention

    async with engine.begin() as conn:
        logger.info(
            'Connection to %s',
            settings.SQLALCHEMY_DATABASE_URI_HIDDEN_PWD
        )
        await conn.run_sync(Model.metadata.create_all)

    async_session_factory = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )
    async_session = scoped_session(async_session_factory)
