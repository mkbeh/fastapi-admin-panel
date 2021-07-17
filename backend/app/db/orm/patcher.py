from inspect import isfunction

from sqlalchemy.sql import Delete, Insert, Select, Update
from sqlalchemy.sql.selectable import Exists

from . import result


select_methods_names = [
    "only",
    "exists",
    "count",
    "with_joined",
    "with_subquery",
]


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
        if isfunction(func) and name not in select_methods_names
    }

    # Patch all
    for name, method in result_methods.items():
        for c in sqlalchemy_crud_classes:
            setattr(c, name, method)

    # Patch select
    select_methods = {
        name: func
        for name, func in result.__dict__.items()
        if isfunction(func) and name in select_methods_names
    }

    for name, method in select_methods.items():
        setattr(Select, name, select_methods[name])
