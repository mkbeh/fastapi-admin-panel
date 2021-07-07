from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from .insepction import InspectionMixin
from .utils import classproperty

if TYPE_CHECKING:
    from db.model import Model


class CRUDMixin(InspectionMixin):
    __abstract__ = True

    @classproperty
    def settable_attributes(cls):
        return cls.columns + cls.hybrid_properties + cls.settable_relations

    def fill(self, **fields):
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
        **fields
    ) -> Model:
        return await cls(**fields).save(db)

    async def update(
        self,
        db: AsyncSession,
        **fields
    ):
        self.fill(**fields)
        return await self.save(db)

    @classmethod
    async def exists(cls, db: AsyncSession, **fields):
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
            select(cls).filter_by(**fields)
        ).select().scalar(db)
