from typing import Union
from sqlalchemy.orm.attributes import InstrumentedAttribute

import schemas


Paths = Union[list[str], list[InstrumentedAttribute]]

SocialRegistrationSchema = Union[
    schemas.RegistrationFromSocialVK,
    schemas.RegistrationFromSocialFacebook,
    schemas.RegistrationFromSocialGoogle,
]
