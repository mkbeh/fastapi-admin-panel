from enum import Flag
from typing import List
from schemas.base import BaseModel


# Additional properties to return via API on get objects of specific table.
class ResultMeta(BaseModel):
    count: int


# Properties to return via API on get objects of specific table.
class ResultSchema(BaseModel):
    result: List = []
    meta: ResultMeta


class ResultResponse(BaseModel):

    class Status(Flag):
        success = True

    result: Status = Status.success
