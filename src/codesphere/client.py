from types import TracebackType

import httpx
from pydantic import SecretStr

from .config import RetryConfig, Settings
from .exceptions import AuthenticationError
from .http_client import APIHttpClient
from .resources.flags import FlagsResource
from .resources.metadata import MetadataResource
from .resources.team import TeamsResource
from .resources.workspace import WorkspacesResource


class CodesphereSDK:
    """Entry point to the Codesphere API.

    Configuration is resolved per argument: explicit constructor argument,
    then the corresponding ``CS_*`` environment variable (``CS_TOKEN``,
    ``CS_BASE_URL``, ``CS_CLIENT_TIMEOUT_CONNECT``/``_READ``; a local
    ``.env`` file is honored), then the built-in default. A missing token
    raises :class:`~codesphere.AuthenticationError` at construction.
    """

    teams: TeamsResource
    workspaces: WorkspacesResource
    metadata: MetadataResource
    flags: FlagsResource

    def __init__(
        self,
        token: str | SecretStr | None = None,
        base_url: str | None = None,
        timeout: httpx.Timeout | None = None,
        retry: RetryConfig | None = None,
        http_client: APIHttpClient | None = None,
    ):
        if http_client is not None:
            self._http_client = http_client
        else:
            settings = Settings()

            resolved_token = self._resolve_token(token, settings)
            resolved_base_url = (
                base_url if base_url is not None else str(settings.base_url)
            )
            resolved_timeout = (
                timeout
                if timeout is not None
                else httpx.Timeout(
                    settings.client_timeout_connect,
                    read=settings.client_timeout_read,
                )
            )
            self._http_client = APIHttpClient(
                token=resolved_token,
                base_url=resolved_base_url,
                timeout=resolved_timeout,
                retry=retry,
            )

        self.teams = TeamsResource(self._http_client)
        self.workspaces = WorkspacesResource(self._http_client)
        self.metadata = MetadataResource(self._http_client)
        self.flags = FlagsResource(self._http_client)

    @staticmethod
    def _resolve_token(token: str | SecretStr | None, settings: Settings) -> SecretStr:
        if token is not None:
            return token if isinstance(token, SecretStr) else SecretStr(token)
        if settings.token is not None:
            return settings.token
        raise AuthenticationError()

    async def open(self) -> None:
        await self._http_client.open()

    async def close(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        await self._http_client.close(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> "CodesphereSDK":
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close(exc_type, exc_val, exc_tb)
