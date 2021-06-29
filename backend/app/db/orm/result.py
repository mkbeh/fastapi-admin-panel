from typing import Optional, Mapping, List, Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row

from db.orm.utils import async_call


def exists(self):
    """
    Syntactic sugar for exists.

    Can be used as an alternative of following:

        is_exist = await exists(
            select(Account).filter_by(**fields)
        ).select().scalar(db)

    Example:

        is_exist = await select(Role) \
            .filter_by(name=role.name) \
            .exists() \
            .scalar(db)

    """
    return sa.exists(self).select()


async def unique(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[Row]:
    return await async_call(
        self, session, parameters, execution_options
    )


async def fetchone(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[Row]:
    """
    Fetch one row.

    When all rows are exhausted, returns None.

    This method is provided for backwards compatibility with
    SQLAlchemy 1.x.x.

    To fetch the first row of a result only, use the
    :meth:`_engine.Result.first` method.  To iterate through all
    rows, iterate the :class:`_engine.Result` object directly.

    :return: a :class:`.Row` object if no filters are applied, or None
     if no rows remain.
    """
    return await async_call(
        self, session, parameters, execution_options
    )


async def fetchmany(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[List[Row]]:
    """Fetch many rows.

    When all rows are exhausted, returns an empty list.

    This method is provided for backwards compatibility with
    SQLAlchemy 1.x.x.

    To fetch rows in groups, use the
    :meth:`._asyncio.AsyncResult.partitions` method.

    :return: a list of :class:`.Row` objects.

    .. seealso::

        :meth:`_asyncio.AsyncResult.partitions`

    """
    return await async_call(
        self, session, parameters, execution_options
    )


async def all(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[List[Row]]:
    """Return all rows in a list.

    Closes the result set after invocation.   Subsequent invocations
    will return an empty list.

    :return: a list of :class:`.Row` objects.

    """
    return await async_call(
        self, session, parameters, execution_options
    )


async def first(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[Row]:
    """Fetch the first row or None if no row is present.

    Closes the result set and discards remaining rows.

    .. note::  This method returns one **row**, e.g. tuple, by default. To
       return exactly one single scalar value, that is, the first column of
       the first row, use the :meth:`_asyncio.AsyncResult.scalar` method,
       or combine :meth:`_asyncio.AsyncResult.scalars` and
       :meth:`_asyncio.AsyncResult.first`.

    :return: a :class:`.Row` object, or None
     if no rows remain.

    .. seealso::

        :meth:`_asyncio.AsyncResult.scalar`

        :meth:`_asyncio.AsyncResult.one`

    """
    return await async_call(
        self, session, parameters, execution_options
    )


async def one_or_none(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
):
    """Return at most one result or raise an exception.

    Returns ``None`` if the result has no rows.
    Raises :class:`.MultipleResultsFound`
    if multiple rows are returned.

    .. versionadded:: 1.4

    :return: The first :class:`.Row` or None if no row is available.

    :raises: :class:`.MultipleResultsFound`

    .. seealso::

        :meth:`_asyncio.AsyncResult.first`

        :meth:`_asyncio.AsyncResult.one`

    """
    return await async_call(
        self, session, parameters, execution_options
    )


async def scalar_one(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Any:
    """Return exactly one scalar result or raise an exception.

    This is equivalent to calling :meth:`_asyncio.AsyncResult.scalars` and
    then :meth:`_asyncio.AsyncResult.one`.

    .. seealso::

        :meth:`_asyncio.AsyncResult.one`

        :meth:`_asyncio.AsyncResult.scalars`

    """
    return await async_call(
        self, session, parameters, execution_options
    )


async def scalar_one_or_none(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
):
    """Return exactly one or no scalar result.

    This is equivalent to calling :meth:`_asyncio.AsyncResult.scalars` and
    then :meth:`_asyncio.AsyncResult.one_or_none`.

    .. seealso::

        :meth:`_asyncio.AsyncResult.one_or_none`

        :meth:`_asyncio.AsyncResult.scalars`

    """
    return await async_call(
        self, session, parameters, execution_options
    )


async def one(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Row:
    """Return exactly one row or raise an exception.

    Raises :class:`.NoResultFound` if the result returns no
    rows, or :class:`.MultipleResultsFound` if multiple rows
    would be returned.

    .. note::  This method returns one **row**, e.g. tuple, by default.
       To return exactly one single scalar value, that is, the first
       column of the first row, use the
       :meth:`_asyncio.AsyncResult.scalar_one` method, or combine
       :meth:`_asyncio.AsyncResult.scalars` and
       :meth:`_asyncio.AsyncResult.one`.

    .. versionadded:: 1.4

    :return: The first :class:`.Row`.

    :raises: :class:`.MultipleResultsFound`, :class:`.NoResultFound`

    .. seealso::

        :meth:`_asyncio.AsyncResult.first`

        :meth:`_asyncio.AsyncResult.one_or_none`

        :meth:`_asyncio.AsyncResult.scalar_one`

    """
    return await async_call(
        self, session, parameters, execution_options
    )


async def scalar(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
):
    """Fetch the first column of the first row, and close the result set.

    Returns None if there are no rows to fetch.

    No validation is performed to test if additional rows remain.

    After calling this method, the object is fully closed,
    e.g. the :meth:`_engine.CursorResult.close`
    method will have been called.

    :return: a Python scalar value , or None if no rows remain.

    """
    return await async_call(
        self, session, parameters, execution_options
    )
