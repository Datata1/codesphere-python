"""
Pydantic models for the Team resource.

Includes the 'active' Team model (with API methods)
and data-only models for creation payloads.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

from ...cs_types.rest.handler import _APIOperationExecutor
from ...cs_types.rest.operations import APIOperation, AsyncCallable


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
