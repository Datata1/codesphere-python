from __future__ import annotations

from functools import cached_property

from ...core.base import BoundModel, CamelModel
from .domain.manager import TeamDomainManager
from .usage.manager import TeamUsageManager


class TeamCreate(CamelModel):
    name: str
    dc: int


class TeamBase(CamelModel):
    id: int
    name: str
    description: str | None = None
    avatar_id: str | None = None
    avatar_url: str | None = None
    is_first: bool
    default_data_center_id: int
    role: int | None = None


class Team(TeamBase, BoundModel):
    async def delete(self) -> None:
        from .operations import _DELETE_TEAM_OP

        await self._execute(_DELETE_TEAM_OP, team_id=self.id)

    @cached_property
    def domains(self) -> TeamDomainManager:
        return TeamDomainManager(self._client(), team_id=self.id)

    @cached_property
    def usage(self) -> TeamUsageManager:
        return TeamUsageManager(self._client(), team_id=self.id)
