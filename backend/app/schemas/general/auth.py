from typing import List, Optional
from pydantic import Field, EmailStr

from extra.enums import SocialTypes
from schemas.base import ConfiguredBaseModel


class LoginParams(ConfiguredBaseModel):
    login: str
    password: str = Field(..., min_length=8, max_length=40, title="password")


class ConfirmAccountParams(ConfiguredBaseModel):
    code: str


class GetTokenBySocialCode(ConfiguredBaseModel):
    code: str


class RequestConfirmationEmailBySocialCode(ConfiguredBaseModel):
    code: str
    email: EmailStr


class RegistationFromSocialBase(ConfiguredBaseModel):
    _social_type: SocialTypes
    # this is our account id
    application_account_id: Optional[int] = None


class GetVKAccessTokenBadRequest(ConfiguredBaseModel):
    error: str
    error_description: str


class RegistrationFromSocialVK(RegistationFromSocialBase):
    _social_type = SocialTypes.vk
    access_token: str
    expires_in: int
    user_id: str
    email: Optional[EmailStr]

    def get_type_and_user_id(self):
        return self._social_type, self.user_id


class GetFacebookAccessTokenBadRequest(ConfiguredBaseModel):
    error_reason: str
    error: str
    error_description: str


class FacebookAccessTokenRequest(ConfiguredBaseModel):
    access_token: str
    token_type: str
    expires_in: int


class RegistrationFromSocialFacebook(RegistationFromSocialBase):
    _social_type = SocialTypes.facebook
    id: str
    name: str
    email: Optional[EmailStr]

    def get_type_and_user_id(self):
        return self._social_type, self.id


class GoogleAccessTokenRequest(ConfiguredBaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: str
    scopes: List[str]


class RegistrationFromSocialGoogle(RegistationFromSocialBase):
    _social_type = SocialTypes.google
    id: str
    email: EmailStr

    def get_type_and_user_id(self):
        return self._social_type, self.id
