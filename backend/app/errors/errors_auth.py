from .common import AppException


class AuthError(AppException):
    """error codes of auth processing logic"""


class LoginError(AuthError):
    """Incorrect username or password"""


class BadToken(AuthError):
    """Bad authorization token"""
    status_code = 401


class TokenExpired(AuthError):
    """Auth token is expired"""
