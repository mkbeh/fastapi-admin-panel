# type: ignore

from __future__ import annotations
from typing import Optional, Mapping, Any, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.sql import Select
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine.row import Row

from extra.types import Paths
from db.orm.utils import async_call, get_model_from_query
from db.mixins.smartquery import smart_query

if TYPE_CHECKING:
    from db.model import Model


def sort(self, *columns: str) -> Select:
    """
    Shortcut for smart_query() method from smartquery mixin

    Example 1:
        User.where(age__gt=18).sort(-id).scalars_all(db)

    Example 2 (with joins):
        User.where(id__gt=0).sort(-id, roles__guid='customer').scalars_all(db)

    """
    query_model = get_model_from_query(self)
    return smart_query(query_model, {}, columns, query=self)


def with_joined(self, *paths: Paths) -> Select:
    """
    Eagerload for simple cases where we need to just
        joined load some relations
    In strings syntax, you can split relations with dot
        due to this SQLAlchemy feature: https://goo.gl/yM2DLX

    Example 1:
        await Comment.with_joined('user', 'post', 'post.comments').first(db)
    Example 2:
        await Comment.with_joined(Comment.user, Comment.post).first(db)
    """
    options = [joinedload(path) for path in paths]
    return self.options(*options)


def with_subquery(self, *paths: Paths) -> Select:
    """
    Eagerload for simple cases where we need to just
        joined load some relations
    In strings syntax, you can split relations with dot
        (it's SQLAlchemy feature)

    Example 1:
        await User.with_subquery('posts', 'posts.comments').scalars_all(db)
    Example 2:
        await User.with_subquery(User.posts, User.comments).scalars_all(db)
    """
    options = [subqueryload(path) for path in paths]
    return self.options(*options)


async def exists(self, db: AsyncSession) -> bool:
    """
    Syntactic sugar for exists.

    Can be used as an alternative of following:

        is_exist = await exists(
            select(Account).filter_by(**fields)
        ).select().scalar(db)

    Example:

        is_exist = await select(Role) \
            .filter_by(name=role.name) \
            .exists(db)

    """
    return await sa.exists(self).select().scalar(db)


async def execute(
    self,
    session: AsyncSession,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Any:
    return await session.execute(self, parameters, execution_options)


async def unique(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[Row]:
    return await async_call(self, session, parameters, execution_options)


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
    return await async_call(self, session, parameters, execution_options)


async def fetchmany(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[list[Row]]:
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
    return await async_call(self, session, parameters, execution_options)


async def all(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[list[Row]]:
    """Return all rows in a list.

    Closes the result set after invocation.   Subsequent invocations
    will return an empty list.

    :return: a list of :class:`.Row` objects.

    """
    return await async_call(self, session, parameters, execution_options)


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
    return await async_call(self, session, parameters, execution_options)


async def one_or_none(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[Row]:
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
    return await async_call(self, session, parameters, execution_options)


async def scalar_one(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Model:
    """Return exactly one scalar result or raise an exception.

    This is equivalent to calling :meth:`_asyncio.AsyncResult.scalars` and
    then :meth:`_asyncio.AsyncResult.one`.

    .. seealso::

        :meth:`_asyncio.AsyncResult.one`

        :meth:`_asyncio.AsyncResult.scalars`

    """
    return await async_call(self, session, parameters, execution_options)


async def scalar_one_or_none(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Optional[Model]:
    """Return exactly one or no scalar result.

    This is equivalent to calling :meth:`_asyncio.AsyncResult.scalars` and
    then :meth:`_asyncio.AsyncResult.one_or_none`.

    .. seealso::

        :meth:`_asyncio.AsyncResult.one_or_none`

        :meth:`_asyncio.AsyncResult.scalars`

    """
    return await async_call(self, session, parameters, execution_options)


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
    return await async_call(self, session, parameters, execution_options)


async def scalar(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Any:
    """Fetch the first column of the first row, and close the result set.

    Returns None if there are no rows to fetch.

    No validation is performed to test if additional rows remain.

    After calling this method, the object is fully closed,
    e.g. the :meth:`_engine.CursorResult.close`
    method will have been called.

    :return: a Python scalar value , or None if no rows remain.

    """
    return await async_call(self, session, parameters, execution_options)


async def scalars(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> Any:
    return await async_call(self, session, parameters, execution_options)


async def scalars_all(
    self,
    session: AsyncSession = None,
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = sa.util.EMPTY_DICT,
) -> list[Model]:
    return (
        await async_call(
            self, session, "scalars", parameters, execution_options
        )
    ).all()
