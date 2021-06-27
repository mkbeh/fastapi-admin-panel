import ujson
from pydantic import BaseModel as PydanticModel


# Base config for all schemas.
class ConfiguredBaseModel(PydanticModel):
    class Config:
        json_loads = ujson.loads
        json_dumps = ujson.dumps
        min_anystr_length = 0


class EmptyStrValidator(PydanticModel):
    class Config:
        min_anystr_length = 1
