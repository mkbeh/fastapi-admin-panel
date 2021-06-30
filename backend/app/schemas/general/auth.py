from pydantic import Field
from schemas.base import ConfiguredBaseModel


class LoginParams(ConfiguredBaseModel):
    login: str
    password: str = Field(..., min_length=8, max_length=40, title="password")
