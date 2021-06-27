from enum import Enum


class TokenPurpose(str, Enum):
    access = 'access'
    refresh = 'refresh'


class Roles(str, Enum):
    customer = 'Customer'
    admin = 'Administrator'


class RegistrationTypes(str, Enum):
    forms = "forms"
    phone = "phone"
    social = "social"


class SocialTypes(str, Enum):
    """Types of oauth services"""
    vk = "vk"
    google = "google"
    facebook = "facebook"
