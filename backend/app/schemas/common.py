from enum import Flag
from typing import List
from schemas.base import ConfiguredBaseModel


# Additional properties to return via API on get objects of specific table.
class ResultMeta(ConfiguredBaseModel):
    count: int


# Properties to return via API on get objects of specific table.
class ResultSchema(ConfiguredBaseModel):
    result: List = []
    meta: ResultMeta


class ResultResponse(ConfiguredBaseModel):

    class Status(Flag):
        success = True

    result: Status = Status.success
