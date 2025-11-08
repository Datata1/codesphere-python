"""
Defines the resource class for the Team API endpoints.
"""

from typing import List, Protocol

from ...core import APIOperation, AsyncCallable, ResourceBase
from .models import Team, TeamCreate


class GetTeamCallable(Protocol):
    async def __call__(self, *, team_id: int) -> Team: ...


class CreateTeamCallable(Protocol):
    async def __call__(self, *, data: TeamCreate) -> Team: ...


class TeamsResource(ResourceBase):
    """
    Provides access to the Team API operations.

    Usage:
        >>> # Access via the main SDK client
        >>> async with CodesphereSDK() as sdk:
        >>>     new_team_data = TeamCreate(name="My Team", dc=1)
        >>>     new_team = await sdk.teams.create(data=new_team_data)
        >>>     team = await sdk.teams.get(team_id=new_team.id)
    """

    list: AsyncCallable[List[Team]]
    """
    Fetches a list of all teams the user belongs to.
    
    Returns:
        List[Team]: A list of Team objects.
    """
    list = APIOperation(
        method="GET",
        endpoint_template="/teams",
        input_model=None,
        response_model=List[Team],
    )

    get: GetTeamCallable
    """
    Fetches a single team by its ID.
    
    Args:
        team_id (int): The unique identifier for the team.
    
    Returns:
        Team: The requested Team object.
    """
    get = APIOperation(
        method="GET",
        endpoint_template="/teams/{team_id}",
        input_model=None,
        response_model=Team,
    )

    create: CreateTeamCallable
    """
    Creates a new team.
    
    Args:
        data (TeamCreate): A :class:`~.models.TeamCreate` object
            containing the new team's information.
    
    Returns:
        Team: The newly created Team object.
    """
    create = APIOperation(
        method="POST",
        endpoint_template="/teams",
        input_model=TeamCreate,
        response_model=Team,
    )
