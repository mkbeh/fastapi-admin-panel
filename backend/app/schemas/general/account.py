from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr, Field, validator

from schemas.base import ConfiguredBaseModel, EmptyStrValidator
from schemas.general.role import RoleInDB


# TODO: email or phone must be specified on create
#   and error when try to clear phone and email on update


# Shared properties.
class AccountBase(ConfiguredBaseModel):
    fullname: str = Field(None, title='Full name')
    email: EmailStr = Field(None, title='Email')
    phone: str = Field(None, title='Phone')

    created_at: datetime = Field(None, title='Created at')
    updated_at: datetime = Field(None, title='Updated at')


# Properties to receive via API on creation.
class AccountCreate(AccountBase, EmptyStrValidator):
    password: str = Field(..., title='Password', min_length=8, max_length=48)
    password2: str = Field(..., title='Retype password', min_length=8, max_length=48)

    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v


# Properties to receive via API on update
class AccountUpdate(AccountBase, EmptyStrValidator):
    password: str = Field(None, title='Password', min_length=8, max_length=48)


class AccountInDBBase(AccountBase):
    id: Optional[int] = None


# Additional properties to return via API
class Account(AccountInDBBase):
    roles: Optional[List[RoleInDB]]


# Additional properties stored in DB
class AccountInDB(AccountInDBBase):
    hashed_password: str
