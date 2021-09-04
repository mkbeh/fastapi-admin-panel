from errors.common import AppException


class SocialError(AppException):
    """ Коды ошибок логики обработки аккаунтов """


class SocilaAlreadyBound(SocialError):
    """Social already bound"""


class SocialNotBound(SocialError):
    """Social not bound"""


class DeletePrimaryAccountDenied(SocialError):
    """Cannot delete the primary account"""


class SocialAlreadyBoundToAnotherUser(SocialError):
    """Account already bound to another user"""
