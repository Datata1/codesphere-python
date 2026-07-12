from pydantic import HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_BASE_URL = "https://codesphere.com/api"


class Settings(BaseSettings):
    """Environment-driven defaults (``CS_*`` variables, optional ``.env``).

    Constructed lazily by :class:`codesphere.CodesphereSDK` — importing the
    package never requires any environment variable to be set.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CS_",
        extra="ignore",
    )

    token: SecretStr | None = None
    base_url: HttpUrl = HttpUrl(DEFAULT_BASE_URL)

    client_timeout_connect: float = 10.0
    client_timeout_read: float = 30.0
