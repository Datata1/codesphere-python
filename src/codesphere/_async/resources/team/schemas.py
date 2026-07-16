from __future__ import annotations

from functools import cached_property

import httpx

from codesphere.models.team import TeamBase
from codesphere.models.team import TeamCreate as TeamCreate

from ...core.base import BoundModel
from .domain.resources import TeamDomainManager
from .usage.resources import TeamUsageManager


class Team(TeamBase, BoundModel):
    async def delete(self, *, timeout: httpx.Timeout | float | None = None) -> None:
        from .operations import _DELETE_TEAM_OP

        await self._execute(_DELETE_TEAM_OP, team_id=self.id, timeout=timeout)

    @cached_property
    def domains(self) -> TeamDomainManager:
        return TeamDomainManager(self._client(), team_id=self.id)

    @cached_property
    def usage(self) -> TeamUsageManager:
        return TeamUsageManager(self._client(), team_id=self.id)
