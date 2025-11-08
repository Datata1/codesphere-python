import httpx
from pydantic import BaseModel
from typing import Optional, Any
from functools import partial

from .config import settings


class APIHttpClient:
    def __init__(self, base_url: str = "https://codesphere.com/api"):
        self._token = settings.token.get_secret_value()
        self._base_url = base_url or str(settings.base_url)
        self.client: Optional[httpx.AsyncClient] = None

        # Dynamically create get, post, put, patch, delete methods
        for method in ["get", "post", "put", "patch", "delete"]:
            setattr(self, method, partial(self.request, method.upper()))

    async def __aenter__(self):
        timeout_config = httpx.Timeout(
            settings.client_timeout_connect, read=settings.client_timeout_read
        )
        self.client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=timeout_config,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        if self.client:
            await self.client.aclose()

    async def request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        if not self.client:
            raise RuntimeError(
                "APIHttpClient must be used within an 'async with' statement."
            )

        # If a 'json' payload is a Pydantic model, automatically convert it.
        if "json" in kwargs and isinstance(kwargs["json"], BaseModel):
            kwargs["json"] = kwargs["json"].model_dump(exclude_none=True)

        print(f"{method} {endpoint} {kwargs}")

        response = await self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response
