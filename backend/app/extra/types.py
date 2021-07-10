from typing import Union
from sqlalchemy.orm.attributes import InstrumentedAttribute


Paths = Union[list[str], list[InstrumentedAttribute]]

