from pydantic import BaseSettings


class MailingSettings(BaseSettings):
    EMAIL_SEND_MODE: bool = False

    COMPANY_EMAIL: str
    COMPANY_NAME: str

    SEND_GRID_KEY: str
