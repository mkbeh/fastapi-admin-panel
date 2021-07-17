from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def in_tx(async_session: AsyncSession) -> AsyncSession:
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
