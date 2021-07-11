from typing import Optional
from pydantic import Field, EmailStr

from extra.enums import SocialTypes
from schemas.base import BaseModel


class LoginParams(BaseModel):
    login: str
    password: str = Field(..., min_length=8, max_length=40, title="password")


class ConfirmAccountParams(BaseModel):
    code: str


class ChangePasswordParams(BaseModel):
    code: str
    new_password: str


class SendEmailChangePassword(BaseModel):
    login: EmailStr


class GetTokenBySocialCode(BaseModel):
    code: str


class RequestConfirmationEmailBySocialCode(BaseModel):
    code: str
    email: EmailStr


class RegistationFromSocialBase(BaseModel):
    _social_type: SocialTypes
    # this is our account id
    application_account_id: Optional[int] = None


class GetVKAccessTokenBadRequest(BaseModel):
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


class GetFacebookAccessTokenBadRequest(BaseModel):
    error_reason: str
    error: str
    error_description: str


class FacebookAccessTokenRequest(BaseModel):
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


class GoogleAccessTokenRequest(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: str
    scopes: list[str]


class RegistrationFromSocialGoogle(RegistationFromSocialBase):
    _social_type = SocialTypes.google
    id: str
    email: EmailStr

    def get_type_and_user_id(self):
        return self._social_type, self.id
