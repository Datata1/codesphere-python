from asyncio import Protocol
from typing import Awaitable, Callable, List
from ..base import ResourceBase, APIOperation
from .models import Team, TeamCreate


class GetTeamCallable(Protocol):
    async def __call__(self, *, team_id: int) -> Team: ...


class CreateTeamCallable(Protocol):
    async def __call__(self, *, data: TeamCreate) -> Team: ...


class DeleteTeamCallable(Protocol):
    async def __call__(self, *, team_id: int) -> None: ...


class TeamsResource(ResourceBase):
    """Contains all API operations for team ressources."""

    list: Callable[[], Awaitable[List[Team]]]
    list = APIOperation(
        method="GET",
        endpoint_template="/teams",
        input_model=None,
        response_model=List[Team],
    )

    get: GetTeamCallable
    get = APIOperation(
        method="GET",
        endpoint_template="/teams/{team_id}",
        input_model=None,
        response_model=Team,
    )

    create: CreateTeamCallable
    create = APIOperation(
        method="POST",
        endpoint_template="/teams",
        input_model=TeamCreate,
        response_model=Team,
    )

    delete: DeleteTeamCallable
    delete = APIOperation(
        method="DELETE",
        endpoint_template="/teams/{team_id}",
        input_model=None,
        response_model=None,
    )
