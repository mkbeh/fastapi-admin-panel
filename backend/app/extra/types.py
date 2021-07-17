from typing import Union
from sqlalchemy.sql import Delete, Insert, Select, Update
from sqlalchemy.sql.selectable import Exists
from sqlalchemy.orm.attributes import InstrumentedAttribute

import schemas


Paths = Union[list[str], list[InstrumentedAttribute]]

SocialRegistrationSchema = Union[
    schemas.RegistrationFromSocialVK,
    schemas.RegistrationFromSocialFacebook,
    schemas.RegistrationFromSocialGoogle,
]

QueryType = Union[Delete, Insert, Select, Update, Exists]
