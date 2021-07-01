from __future__ import annotations
from typing import TYPE_CHECKING
from functools import wraps

from sqlalchemy import func as sa_func
from sqlalchemy.future import select

from schemas import ResultSchema, ResultMeta


if TYPE_CHECKING:
    from db.model import Model


def add_count(model: Model):
    """
    This decorator can be accepted only for all read many rows methods.
    Gets a list of model objects and adds a count of all objects in this
    model to the resulting schema.
    """
    def decorator(func):
        @wraps(func)
        async def create_new_schema(*args, **kwargs):
            instances, db = await func(*args, **kwargs)
            total_rows = await select(sa_func.count(model.id)).scalar(db)
            return ResultSchema(
                result=instances,
                meta=ResultMeta(count=total_rows)
            )
        return create_new_schema
    return decorator
