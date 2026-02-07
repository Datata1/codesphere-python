from typing import List

from pydantic import Field

from .operations import (
    _CREATE_TEAM_OP,
    _GET_TEAM_OP,
    _LIST_TEAMS_OP,
)

from ...core.base import ResourceList
from ...core import AsyncCallable, ResourceBase
from .schemas import Team, TeamCreate


class TeamsResource(ResourceBase):
    list_team_op: AsyncCallable[ResourceList[Team]] = Field(
        default=_LIST_TEAMS_OP, exclude=True
    )

    async def list(self) -> List[Team]:
        result = await self.list_team_op()
        return result.root

    get_team_op: AsyncCallable[Team] = Field(default=_GET_TEAM_OP, exclude=True)

    async def get(self, team_id: int) -> Team:
        return await self.get_team_op(team_id=team_id)

    create_team_op: AsyncCallable[Team] = Field(default=_CREATE_TEAM_OP, exclude=True)

    async def create(self, payload: TeamCreate) -> Team:
        return await self.create_team_op(data=payload)
