from enum import Flag
from schemas.base import BaseModel


# Additional properties to return via API on get objects of specific table.
class ResultMeta(BaseModel):
    count: int


# Properties to return via API on get objects of specific table.
class ResultSchema(BaseModel):
    result: list = []
    meta: ResultMeta


class ResultResponse(BaseModel):

    class Status(Flag):
        success = True

    result: Status = Status.success
