from __future__ import annotations
from pydantic import BaseModel, PrivateAttr
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from ...client import APIHttpClient


class Domain(BaseModel):
    _http_client: Optional[APIHttpClient] = PrivateAttr(default=None)

    id: str
    name: str
    verified_at: Optional[datetime] = None

    async def delete(self) -> None:
        """Deletes this specific domain instance via the API."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")
        if not self.id:
            raise ValueError("Cannot delete a domain without an ID.")

        await self._http_client.delete(f"/domains/{self.id}")
        print(f"Domain '{self.name}' has been deleted.")

    async def save(self) -> None:
        """Updates this domain with its current data."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")
        if not self.id:
            raise ValueError("Cannot update a domain without an ID.")

        update_data = self.model_dump(exclude={"id"})

        await self._http_client.put(f"/domains/{self.id}", json=update_data)
        print(f"Domain '{self.name}' has been updated.")
