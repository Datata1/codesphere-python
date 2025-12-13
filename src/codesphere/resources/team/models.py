"""
Pydantic models for the Team resource.

Includes the 'active' Team model (with API methods)
and data-only models for creation payloads.
"""

from __future__ import annotations
from functools import cached_property
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Optional

from .domain.models import TeamDomainManager
from ...core import _APIOperationExecutor, APIOperation, AsyncCallable

if TYPE_CHECKING:
    pass


class TeamCreate(BaseModel):
    """Data payload required for creating a new team."""

    name: str
    dc: int


class TeamBase(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    avatarId: Optional[str] = None
    avatarUrl: Optional[str] = None
    isFirst: bool
    defaultDataCenterId: int
    role: Optional[int] = None


class Team(TeamBase, _APIOperationExecutor):
    """
    Represents a complete, 'active' team object returned from the API.

    This model includes methods to interact with the resource directly.

    Usage:
        >>> # Get a team instance
        >>> team = await sdk.teams.get(team_id=123)
        >>> # Call methods on it
        >>> await team.delete()
    """

    delete: AsyncCallable[None]
    """
    Deletes this team via the API.
    
    .. warning::
       This is a destructive operation and cannot be undone.
    """
    delete = Field(
        default=APIOperation(
            method="DELETE",
            endpoint_template="/teams/{id}",
            response_model=None,
        ),
        exclude=True,
    )

    @cached_property
    def domains(self) -> TeamDomainManager:
        """
        Provides access to domain management for this team.

        Usage:
            >>> team = await sdk.teams.get(id=123)
            >>> await team.domains.list()
            >>> await team.domains.create("example.com")
        """
        if not self._http_client:
            raise RuntimeError("Cannot access 'domains' on a detached model.")

        return TeamDomainManager(http_client=self._http_client, team_id=self.id)
