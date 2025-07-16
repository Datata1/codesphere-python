from __future__ import annotations
from pydantic import BaseModel, PrivateAttr, model_validator
from typing import Optional, TYPE_CHECKING

from ..domain.resource import DomainsResource

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


class TeamInList(TeamBase):
    """Represents a team as it appears in the list response."""

    role: int


class Team(TeamBase):
    """
    Represents a complete, single team object (detail view).
    This is the "active" model with methods.
    """

    _http_client: Optional[APIHttpClient] = PrivateAttr(default=None)
    _domains: Optional[DomainsResource] = PrivateAttr(default=None)

    @model_validator(mode="after")
    def setup_sub_resources(self) -> "Team":
        """Creates the sub-resources after initialization."""
        if self._http_client:
            self._domains = DomainsResource(
                http_client=self._http_client, team_id=str(self.id)
            )
        return self

    async def delete(self) -> None:
        """Deletes this team via the API."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")
        await self._http_client.delete(f"/teams/{self.id}")
