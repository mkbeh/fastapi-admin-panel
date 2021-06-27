import re
from typing import Any

from sqlalchemy.ext.declarative import as_declarative, declared_attr

from .mixins import ReprMixin


@as_declarative()
class Model(ReprMixin):
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically"""
        pattern = re.compile("[A-Z][^A-Z]*")
        return "_".join(x.lower() for x in re.findall(pattern, cls.__name__))
