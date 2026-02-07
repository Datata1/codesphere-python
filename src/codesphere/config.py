from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CS_",
        extra="ignore",
    )

    token: SecretStr
    base_url: HttpUrl = "https://codesphere.com/api"

    client_timeout_connect: float = 10.0
    client_timeout_read: float = 30.0


settings = Settings()
