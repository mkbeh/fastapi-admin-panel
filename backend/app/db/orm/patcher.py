from inspect import isfunction

from sqlalchemy.sql import Delete, Insert, Select, Update
from sqlalchemy.sql.selectable import Exists

from . import result


def patch_sqlalchemy_crud():
    sqlalchemy_crud_classes = (
        Insert,
        Update,
        Select,
        Delete,
        Exists,
    )

    result_methods = {
        name: func
        for name, func in result.__dict__.items()
        if isfunction(func)
    }

    # Patch all
    for name, method in result_methods.items():
        for c in sqlalchemy_crud_classes:
            setattr(c, name, method)

    # Patch select
    setattr(Select, 'exists', result_methods['exists'])
