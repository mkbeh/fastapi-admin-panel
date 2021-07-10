from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Any

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
        db: AsyncSession,
        flush: bool = True,
        refresh: bool = False
    ) -> Model:
        db.add(self)
        if flush:
            await db.flush()
        if refresh:
            await db.refresh(self)
        return self

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        **fields: str
    ) -> Model:
        return await cls(**fields).save(db)

    async def update(
        self,
        db: AsyncSession,
        **fields: str
    ) -> Model:
        self.fill(**fields)
        return await self.save(db)

    @classmethod
    async def get_or_create(
        cls,
        db: Optional[AsyncSession] = None,
        defaults: Optional[dict] = None,
        **kwargs: Any,
    ) -> Tuple[Model, bool]:
        """
        Fetches the object if exists (filtering on the provided parameters),
        else creates an instance with any unspecified parameters as default values.
        """
        if defaults is None:
            defaults = {}
        try:
            instance = await cls.where(**kwargs).one(db)
            return instance, False
        except NoResultFound:
            kwargs |= defaults or {}
            return await cls.create(db, **kwargs), True

    @classmethod
    async def update_or_create(
        cls,
        db: Optional[AsyncSession] = None,
        defaults: Optional[dict] = None,
        **kwargs: Any,
    ) -> Tuple[Model, bool]:
        """
        A convenience method for updating an object with the given
        kwargs, creating a new one if necessary.
        """
        if defaults is None:
            defaults = {}
        try:
            instance = await cls.where(**kwargs).one(db)
        except NoResultFound:
            kwargs |= defaults or {}
            return await cls.create(db, **kwargs), True
        else:
            await instance.update(**defaults)
            return instance, False

    @classmethod
    async def exists(
        cls,
        db: AsyncSession,
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
        return await exists(
            cls.where(**fields)
        ).select().scalar(db)
