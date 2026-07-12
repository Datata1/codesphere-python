from ....core.base import ResourceBase
from ....http_client import APIHttpClient
from .operations import _CREATE_OP, _GET_OP, _LIST_OP, _UPDATE_OP, _UPDATE_WS_OP
from .resources import Domain
from .schemas import CustomDomainConfig, DomainRouting, RoutingMap


class TeamDomainManager(ResourceBase):
    def __init__(self, http_client: APIHttpClient, team_id: int):
        super().__init__(http_client)
        self.team_id = team_id

    async def list(self) -> list[Domain]:
        result = await self._execute(_LIST_OP, team_id=self.team_id)
        return result.root

    async def get(self, name: str) -> Domain:
        return await self._execute(_GET_OP, team_id=self.team_id, name=name)

    async def create(self, name: str) -> Domain:
        return await self._execute(_CREATE_OP, team_id=self.team_id, name=name)

    async def update(self, name: str, config: CustomDomainConfig) -> Domain:
        return await self._execute(
            _UPDATE_OP, team_id=self.team_id, name=name, data=config
        )

    async def update_workspace_connections(
        self, name: str, connections: DomainRouting | RoutingMap
    ) -> Domain:
        payload = (
            connections.root if isinstance(connections, DomainRouting) else connections
        )
        return await self._execute(
            _UPDATE_WS_OP, team_id=self.team_id, name=name, data=payload
        )
