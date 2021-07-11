from core.settings import settings
from core.security import generate_confirmation_code

from .sender import BaseMessage


# To developers: KISS is much more important than DRY!

# So do OOP-inheritance ONLY if your new classes has same validation fields,
# same purpose AND MANY common logic.
# If you have to do some same validation without any complexity, do it in
# separate classes without inheritance, please.
# The class is much more readable and error-resilient if it has smaller
# inheritance chain.
# This can be extended to other things, like pydantic models, email messages, etc.


class ConfirmAccountMessage(BaseMessage):
    template_name = 'confirm.html'

    class validation(BaseMessage.validation):
        subject: str = 'Confirm registration'
        account_id: int

    def get_context(self) -> dict:
        code = generate_confirmation_code(
            account_id=self.schema.account_id
        )
        return {'url': f'{settings.SERVER_DOMAIN}/webhooks/confirm/account?code={code}'}


class ChangePasswordMessage(BaseMessage):
    template_name = 'forget_password.html'

    class validation(BaseMessage.validation):
        subject: str = 'Change password'
        account_id: int

    def get_context(self) -> dict:
        code = generate_confirmation_code(
            account_id=self.schema.account_id
        )
        return {'url': f'{settings.SERVER_DOMAIN}/change-password?code={code}'}


class PasswordWasChangedMessage(BaseMessage):
    template_name = 'changed_password.html'

    class validation(BaseMessage.validation):
        subject: str = 'Your password has been changed'


class SuccessfulRegistrationMessage(BaseMessage):
    template_name = 'registration.html'

    class validation(BaseMessage.validation):
        subject: str = 'You have successfully registered'
        url: str = f'{settings.SERVER_DOMAIN}/personal_area'


class ChangeBankCardMessage(BaseMessage):
    template_name = 'change_bank_card.html'

    class validation(BaseMessage.validation):
        subject: str = 'Failed to process payment'
        account_id: int

    def get_context(self) -> dict:
        account_id = self.schema.account_id
        return {
            'url': f'{settings.API_URL}/payments/change_bank_card/{account_id}'
        }
