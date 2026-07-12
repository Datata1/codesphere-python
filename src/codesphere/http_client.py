import logging
from types import TracebackType
from typing import Any

import httpx
from pydantic import SecretStr

from .exceptions import NetworkError, TimeoutError, raise_for_status

log = logging.getLogger(__name__)


class APIHttpClient:
    """Thin async transport around httpx.

    Receives its full configuration from the caller (the SDK resolves
    arguments, environment variables, and defaults) and owns nothing but
    the connection lifecycle and error mapping.
    """

    def __init__(self, *, token: SecretStr, base_url: str, timeout: httpx.Timeout):
        self._token = token.get_secret_value()
        self._base_url = base_url
        self._client: httpx.AsyncClient | None = None

        self._timeout_config = timeout
        self._client_config: dict[str, Any] = {
            "base_url": self._base_url,
            "headers": {"Authorization": f"Bearer {self._token}"},
            "timeout": self._timeout_config,
        }

    def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError(
                "Client is not open. Please use 'async with sdk:' "
                "or call 'await sdk.open()' before making requests."
            )
        return self._client

    async def open(self) -> None:
        if not self._client:
            self._client = httpx.AsyncClient(**self._client_config)
            await self._client.__aenter__()

    async def close(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None

    async def __aenter__(self) -> "APIHttpClient":
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close(exc_type, exc_val, exc_tb)

    async def request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        client = self._get_client()

        log.debug(f"Request: {method} {endpoint}")
        log.debug(f"Request kwargs: {kwargs}")

        try:
            response = await client.request(method, endpoint, **kwargs)
            log.debug(
                f"Response: {response.status_code} {response.reason_phrase} "
                f"for {method} {endpoint}"
            )

            raise_for_status(response)
            return response

        except httpx.TimeoutException as e:
            log.error(f"Request timeout for {method} {endpoint}: {e}")
            raise TimeoutError(f"Request to {endpoint} timed out.") from e
        except httpx.ConnectError as e:
            log.error(f"Connection error for {method} {endpoint}: {e}")
            raise NetworkError(
                f"Failed to connect to the API: {e}",
                original_error=e,
            ) from e
        except httpx.RequestError as e:
            log.error(f"Network error for {method} {endpoint}: {e}")
            raise NetworkError(
                f"A network error occurred: {e}",
                original_error=e,
            ) from e
