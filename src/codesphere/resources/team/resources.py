from ...core import ResourceBase
from .operations import (
    _CREATE_TEAM_OP,
    _GET_TEAM_OP,
    _LIST_TEAMS_OP,
)
from .schemas import Team, TeamCreate


class TeamsResource(ResourceBase):
    async def list(self) -> list[Team]:
        result = await self._execute(_LIST_TEAMS_OP)
        return result.root

    async def get(self, team_id: int) -> Team:
        return await self._execute(_GET_TEAM_OP, team_id=team_id)

    async def create(self, payload: TeamCreate) -> Team:
        return await self._execute(_CREATE_TEAM_OP, data=payload)
