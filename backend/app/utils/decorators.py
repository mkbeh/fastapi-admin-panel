from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar
from functools import wraps

from sqlalchemy import func as sa_func
from sqlalchemy.future import select

from schemas import ResultSchema, ResultMeta
from schemas.base import BaseModel

if TYPE_CHECKING:
    from db.model import Model


ModelSchema = TypeVar('ModelSchema', bound=BaseModel)


def add_count(
    response_model: Model,
    response_schema: ModelSchema
):
    """
    This decorator can be accepted only for all read many rows methods.
    Gets a list of model objects and adds a count of all objects in this
    model to the resulting schema.
    """
    def decorator(func):
        @wraps(func)
        async def create_new_schema(*args, **kwargs):
            instances, db = await func(*args, **kwargs)
            total_rows = await select(sa_func.count(response_model.id)).scalar(db)
            return ResultSchema(
                result=[response_schema.from_orm(x) for x in instances],
                meta=ResultMeta(count=total_rows)
            )
        return create_new_schema
    return decorator
