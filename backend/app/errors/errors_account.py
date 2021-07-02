from .common import AppException


class AccountError(AppException):
    """Error codes of account processing logic"""


class AccountAlreadyExist(AccountError):
    """Account with this email or phone exists"""


class EmailIsExists(AccountError):
    """This email is already in use in the system"""


class NotEnoughPrivileges(AccountError):
    """The account doesn't have enough privileges"""
    status_code = 401


class InactiveAccount(AccountError):
    """Inactive account"""


class AccountIsNotConfirmed(AccountError):
    """Account not verified"""


class SocialLoginFailed(AccountError):
    """Social login failed"""


class UnknownSocialType(AccountError):
    """Unknown type of social integration"""


class SocialUserEmailIsNotConfirmed(AccountError):
    """Email for login via social network is not confirmed"""


class BadSocialCode(AccountError):
    """Invalid login code"""
