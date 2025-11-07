from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    API Client Settings

    TODO: add List of available env vars
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="CS_"
    )

    token: SecretStr
    base_url: HttpUrl = "https://codesphere.com/api"

    client_timeout_connect: float = 10.0
    client_timeout_read: float = 30.0


settings = Settings()
