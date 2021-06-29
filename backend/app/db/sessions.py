from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.settings import settings


engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


@asynccontextmanager
async def in_transaction() -> AsyncSession:
    """
    Transaction context manager.

    You can run your code inside ``async with in_transaction() as tx:``
    statement to run it into one transaction. If error occurs transaction
    will rollback.
    """
    session = async_session()
    await session.begin()
    try:
        yield session
        await session.commit()
    except BaseException:
        await session.rollback()
        raise
    finally:
        await session.close()
