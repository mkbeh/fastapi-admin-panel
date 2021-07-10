from enum import Enum
from typing import Callable, Union

from fastapi import HTTPException

import errors
from errors.common import AppException
from schemas.base import BaseModel


class StrEnum(str, Enum):
    pass


Errors = StrEnum(
    "Errors",
    {
        key: key
        for key, val in errors.__dict__.items()
        if callable(val) or isinstance(val, Exception)
    },
)


class Error(BaseModel):
    code: Errors  # type: ignore
    detail: str


def with_errors(
    *errors: Union[AppException, HTTPException, Callable[..., HTTPException]]
):
    d = {}
    for err in errors:
        err_factory = err
        if callable(err_factory):
            err = err_factory()
        if isinstance(err_factory, AppException) or (
            isinstance(err_factory, type) and issubclass(err_factory, AppException)
        ):
            err = HTTPException(
                status_code=err_factory.status_code, detail=err_factory.__doc__
            )
        if isinstance(err_factory, HTTPException):
            err_factory.__name__ = "HTTPException"
        if err.status_code not in d:
            d[err.status_code] = dict(description="Code | Detail\n - | -", model=Error)
        d[err.status_code][
            "description"
        ] += f"\n***{err_factory.__name__}***| {err.detail}"
    return d
