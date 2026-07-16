import httpx

from ....core.base import TeamScopedResource
from .operations import _CREATE_OP, _GET_OP, _LIST_OP, _UPDATE_OP, _UPDATE_WS_OP
from .schemas import CustomDomainConfig, Domain, DomainRouting, RoutingMap


class TeamDomainManager(TeamScopedResource):
    async def list(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> list[Domain]:
        result = await self._execute(_LIST_OP, team_id=self.team_id, timeout=timeout)
        return result.root

    async def get(
        self, name: str, *, timeout: httpx.Timeout | float | None = None
    ) -> Domain:
        return await self._execute(
            _GET_OP, team_id=self.team_id, name=name, timeout=timeout
        )

    async def create(
        self, name: str, *, timeout: httpx.Timeout | float | None = None
    ) -> Domain:
        return await self._execute(
            _CREATE_OP, team_id=self.team_id, name=name, timeout=timeout
        )

    async def update(
        self,
        name: str,
        config: CustomDomainConfig,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> Domain:
        return await self._execute(
            _UPDATE_OP, team_id=self.team_id, name=name, data=config, timeout=timeout
        )

    async def update_workspace_connections(
        self,
        name: str,
        connections: DomainRouting | RoutingMap,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> Domain:
        payload = (
            connections.root if isinstance(connections, DomainRouting) else connections
        )
        return await self._execute(
            _UPDATE_WS_OP,
            team_id=self.team_id,
            name=name,
            data=payload,
            timeout=timeout,
        )
