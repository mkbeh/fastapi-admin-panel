from fastapi import HTTPException, status

from db.model import Model


class AppException(Exception):
    """Errors of processing logic"""
    status_code = 400


def object_not_found(
    model: Model,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> HTTPException:
    # 400 - because this is an expected error.
    # All unexpected errors must be 404 or 500.
    return HTTPException(
        status_code=status_code,
        detail=f'{model.__name__} is not found',
    )
