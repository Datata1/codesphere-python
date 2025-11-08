from functools import partial
import logging
import httpx
from pydantic import BaseModel
from typing import Optional, Any
from ...config import settings

log = logging.getLogger(__name__)


class APIHttpClient:
    def __init__(self, base_url: str = "https://codesphere.com/api"):
        self._token = settings.token.get_secret_value()
        self._base_url = base_url or str(settings.base_url)
        self._client: Optional[httpx.AsyncClient] = None

        self._timeout_config = httpx.Timeout(
            settings.client_timeout_connect, read=settings.client_timeout_read
        )
        self._client_config = {
            "base_url": self._base_url,
            "headers": {"Authorization": f"Bearer {self._token}"},
            "timeout": self._timeout_config,
        }

        for method in ["get", "post", "put", "patch", "delete"]:
            setattr(self, method, partial(self.request, method.upper()))

    def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError(
                "Client is not open. Please use 'async with sdk:' "
                "or call 'await sdk.open()' before making requests."
            )
        return self._client

    async def open(self):
        if not self._client:
            self._client = httpx.AsyncClient(**self._client_config)
            await self._client.__aenter__()

    async def close(self, exc_type=None, exc_val=None, exc_tb=None):
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
            self._client = None

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        await self.close(exc_type, exc_val, exc_tb)

    async def request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        client = self._get_client()

        if "json" in kwargs and isinstance(kwargs["json"], BaseModel):
            kwargs["json"] = kwargs["json"].model_dump(exclude_none=True)

        log.debug(f"Request: {method} {endpoint}")
        log.debug(f"Request kwargs: {kwargs}")

        try:
            response = await client.request(method, endpoint, **kwargs)
            log.debug(
                f"Response: {response.status_code} {response.reason_phrase} for {method} {endpoint}"
            )

            response.raise_for_status()
            return response

        except httpx.HTTPStatusError as e:
            log.error(
                f"HTTP Error {e.response.status_code} for {e.request.method} {e.request.url}"
            )
            try:
                log.error(f"Error Response Body: {e.response.json()}")
            except Exception:
                log.error(f"Error Response Body (non-json): {e.response.text}")
            raise e
        except Exception as e:
            log.error(f"An unexpected error occurred: {e}")
            raise e
