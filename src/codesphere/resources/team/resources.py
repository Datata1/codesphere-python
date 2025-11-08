from typing import Awaitable, Callable, List, Protocol
from ..base import ResourceBase, APIOperation
from .models import Team, TeamCreate


class GetTeamCallable(Protocol):
    async def __call__(self, *, team_id: int) -> Team: ...


class CreateTeamCallable(Protocol):
    async def __call__(self, *, data: TeamCreate) -> Team: ...


class TeamsResource(ResourceBase):
    """Contains all API operations for team ressources."""

    list: Callable[[], Awaitable[List[Team]]]
    """
    Fetches all teams.
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
        data (TeamCreate): The data payload for the new team.
    
    Returns:
        Team: The newly created Team object.
    """
    create = APIOperation(
        method="POST",
        endpoint_template="/teams",
        input_model=TeamCreate,
        response_model=Team,
    )
