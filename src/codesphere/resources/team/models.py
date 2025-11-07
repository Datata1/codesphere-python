from __future__ import annotations
from pydantic import BaseModel, PrivateAttr
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...client import APIHttpClient


class TeamCreate(BaseModel):
    """Defines the request body for creating a team."""

    name: str
    dc: int


class TeamBase(BaseModel):
    """Contains all fields that appear in almost every team response."""

    id: int
    name: str
    description: Optional[str] = None
    avatarId: Optional[str] = None
    avatarUrl: Optional[str] = None
    isFirst: bool
    defaultDataCenterId: int
    role: Optional[int] = None


class Team(TeamBase):
    """
    Represents a complete, single team object (detail view).
    This is the "active" model with methods.
    """

    _http_client: Optional[APIHttpClient] = PrivateAttr(default=None)

    async def delete(self) -> None:
        """Deletes this team via the API."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")
        await self._http_client.delete(f"/teams/{self.id}")
