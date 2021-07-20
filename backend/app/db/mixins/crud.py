from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Any, Iterable

from sqlalchemy import exists
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from .inspection import InspectionMixin
from .utils import classproperty

if TYPE_CHECKING:
    from db.model import Model


class CRUDMixin(InspectionMixin):
    __abstract__ = True

    @classproperty
    def settable_attributes(cls) -> list[str]:
        return cls.columns + cls.hybrid_properties + cls.settable_relations

    def fill(self, **fields: str) -> Model:
        for name in fields.keys():
            if name in self.settable_attributes:
                setattr(self, name, fields[name])
            else:
                raise KeyError("Attribute '{}' doesn't exist".format(name))

        return self

    async def save(
        self,
        session: AsyncSession,
        flush: bool = True,
        refresh: bool = False
    ) -> Model:
        session.add(self)
        if flush:
            await session.flush()
        if refresh:
            await session.refresh(self)
        return self

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        **fields: str
    ) -> Model:
        return await cls().fill(**fields).save(session)

    @classmethod
    async def bulk_create(
        cls,
        session: AsyncSession,
        objects: Iterable[Model]
    ):
        """Add and create the given collection of instances."""
        session.add_all(objects)
        await session.flush()


    async def update(
        self,
        session: AsyncSession,
        **fields: str
    ) -> Model:
        self.fill(**fields)
        return await self.save(session)

    @classmethod
    async def get_or_create(
        cls,
        session: Optional[AsyncSession] = None,
        defaults: Optional[dict] = None,
        **kwargs: Any,
    ) -> tuple[Model, bool]:
        """
        Fetches the object if exists (filtering on the provided parameters),
        else creates an instance with any unspecified parameters as default values.
        """
        if defaults is None:
            defaults = {}
        try:
            instance = await cls.where(**kwargs).one(session)
            return instance, False
        except NoResultFound:
            kwargs |= defaults or {}
            return await cls.create(session, **kwargs), True

    @classmethod
    async def update_or_create(
        cls,
        session: Optional[AsyncSession] = None,
        defaults: Optional[dict] = None,
        **kwargs: Any,
    ) -> tuple[Model, bool]:
        """
        A convenience method for updating an object with the given
        kwargs, creating a new one if necessary.
        """
        if defaults is None:
            defaults = {}
        try:
            instance = await cls.where(**kwargs).one(session)
        except NoResultFound:
            kwargs |= defaults or {}
            return await cls.create(session, **kwargs), True
        else:
            await instance.update(session, **defaults)
            return instance, False

    @classmethod
    async def find(
        cls,
        session: Optional[AsyncSession],
        id: int,
    ) -> Model:
        """
        Find record by id.

        Args:
            id_ (int): Primary key

        Raises: NoResultFound
        """
        instance = await session.get(cls, id)
        if not instance:
            raise NoResultFound
        return instance

    @classmethod
    async def find_or_none(
        cls,
        session: Optional[AsyncSession],
        id: int,
    ) -> Model:
        """
        Find record by id.

        Args:
            id_ (int): Primary key
        """
        return await session.get(cls, id)

    @classmethod
    async def exists(
        cls,
        session: AsyncSession,
        **fields: str
    ) -> bool:
        """
        Syntactic sugar for exists.

        Can be used as an alternative of following:

            is_exist = await exists(
                select(Account).filter_by(**fields)
            ).select().scalar(db)

        Example:

            is_exist = await Account \
                .exists(db, email="jondoe@gmail.com")

        """
        return await exists(cls.where(**fields)).select().scalar(session)
