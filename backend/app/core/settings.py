import os

from .conf import AuthSettings, DatabaseSettings, MailingSettings, ServerSettings


class Settings(ServerSettings, DatabaseSettings, AuthSettings, MailingSettings):
    ...

    class Config:
        case_sensitive = True
        env_file = os.getenv("ENV_FILE")
        env_file_encoding = "utf-8"


settings = Settings()
