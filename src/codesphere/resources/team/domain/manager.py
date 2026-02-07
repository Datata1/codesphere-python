from typing import List, Union

from pydantic import Field

from ....core.base import ResourceList
from ....core.handler import _APIOperationExecutor
from ....core.operations import AsyncCallable
from ....http_client import APIHttpClient
from .operations import _CREATE_OP, _GET_OP, _LIST_OP, _UPDATE_OP, _UPDATE_WS_OP
from .resources import Domain
from .schemas import CustomDomainConfig, DomainRouting, RoutingMap


class TeamDomainManager(_APIOperationExecutor):
    def __init__(self, http_client: APIHttpClient, team_id: int):
        self._http_client = http_client
        self.team_id = team_id

    list_op: AsyncCallable[ResourceList[Domain]] = Field(
        default=_LIST_OP.model_copy(update={"response_model": ResourceList[Domain]}),
        exclude=True,
    )

    async def list(self) -> List[Domain]:
        result = await self.list_op()
        return result.root

    get_op: AsyncCallable[Domain] = Field(
        default=_GET_OP.model_copy(update={"response_model": Domain}),
        exclude=True,
    )

    async def get(self, name: str) -> Domain:
        return await self.get_op(name=name)

    create_op: AsyncCallable[Domain] = Field(
        default=_CREATE_OP.model_copy(update={"response_model": Domain}),
        exclude=True,
    )

    async def create(self, name: str) -> Domain:
        return await self.create_op(name=name)

    update_op: AsyncCallable[Domain] = Field(
        default=_UPDATE_OP.model_copy(update={"response_model": Domain}),
        exclude=True,
    )

    async def update(self, name: str, config: CustomDomainConfig) -> Domain:
        return await self.update_op(name=name, data=config)

    update_ws_op: AsyncCallable[Domain] = Field(
        default=_UPDATE_WS_OP.model_copy(update={"response_model": Domain}),
        exclude=True,
    )

    async def update_workspace_connections(
        self, name: str, connections: Union[DomainRouting, RoutingMap]
    ) -> Domain:
        payload = (
            connections.root if isinstance(connections, DomainRouting) else connections
        )
        return await self.update_ws_op(name=name, data=payload)
