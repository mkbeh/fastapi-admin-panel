import os
from .conf import (
    ServerSettings,
    DatabaseSettings,
    AuthSettings,
    MailingSettings,
)


class Settings(
    ServerSettings, DatabaseSettings,
    AuthSettings, MailingSettings,
):
    ...

    class Config:
        case_sensitive = True
        env_file = os.getenv("ENV_FILE")
        env_file_encoding = "utf-8"


settings = Settings()
