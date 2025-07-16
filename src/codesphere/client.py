import os
import httpx
from pydantic import BaseModel
from typing import Optional, Any

from .resources.exceptions.exceptions import AuthenticationError


class APIHttpClient:
    def __init__(self, base_url: str = "https://codesphere.com/api"):
        auth_token = os.environ.get("CS_TOKEN")

        if not auth_token:
            raise AuthenticationError()

        self._token = auth_token
        self._base_url = base_url
        self.client: Optional[httpx.Client] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self._base_url, headers={"Authorization": f"Bearer {self._token}"}
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        if self.client:
            await self.client.aclose()

    async def request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        if not self.client:
            raise RuntimeError("APIHttpClient must be used within a 'with' statement.")
        print(f"{method} {endpoint} {kwargs}")

        response = await self.client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        return response

    async def get(self, endpoint: str, json: Optional[dict] = None) -> httpx.Response:
        json_data = json.model_dump() if json else None
        return await self.request("GET", endpoint, json=json_data)

    async def post(
        self, endpoint: str, json: Optional[BaseModel] = None
    ) -> httpx.Response:
        json_data = json.model_dump() if json else None
        return await self.request("POST", endpoint, json=json_data)

    async def put(
        self, endpoint: str, json: Optional[BaseModel] = None
    ) -> httpx.Response:
        json_data = json.model_dump() if json else None
        return await self.request("PUT", endpoint, json=json_data)

    async def delete(self, endpoint: str) -> httpx.Response:
        return await self.request("DELETE", endpoint)
