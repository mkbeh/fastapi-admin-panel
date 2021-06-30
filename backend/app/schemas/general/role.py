from typing import Optional
from pydantic import Field

from extra.enums import Roles
from schemas.base import ConfiguredBaseModel, EmptyStrValidator


# Shared properties.
class RoleBase(ConfiguredBaseModel):
    name: Roles = Field(None, title='name')


# Properties to receive via API on creation.
class RoleCreate(RoleBase, EmptyStrValidator):
    name: Roles = Field(..., title='name')


# Properties to receive via API on update
class RoleUpdate(RoleBase, EmptyStrValidator):
    name: Roles = Field(None, title='name')


class RoleInDBBase(RoleBase):
    id: Optional[int] = None


# Additional properties to return via API
class Role(RoleInDBBase):
    guid: str


# Additional properties stored in DB
class RoleInDB(RoleInDBBase):
    guid: str
