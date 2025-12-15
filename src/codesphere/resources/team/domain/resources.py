from __future__ import annotations
import logging
from typing import Union
from pydantic import Field

from .operations import (
    _DELETE_OP,
    _UPDATE_OP,
    _UPDATE_WS_OP,
    _VERIFY_OP,
)
from .schemas import (
    CustomDomainConfig,
    DomainBase,
    DomainRouting,
    DomainVerificationStatus,
    RoutingMap,
)

from ....core.handler import _APIOperationExecutor
from ....core.operations import AsyncCallable
from ....utils import update_model_fields


log = logging.getLogger(__name__)


class Domain(DomainBase, _APIOperationExecutor):
    update_op: AsyncCallable[None] = Field(default=_UPDATE_OP, exclude=True)
    update_workspace_connections_op: AsyncCallable[None] = Field(
        default=_UPDATE_WS_OP, exclude=True
    )
    verify_domain_op: AsyncCallable[None] = Field(default=_VERIFY_OP, exclude=True)
    delete_domain_op: AsyncCallable[None] = Field(default=_DELETE_OP, exclude=True)

    async def update(self, data: CustomDomainConfig) -> Domain:
        payload = data.model_dump(exclude_unset=True, by_alias=True)
        response = await self.update_op(data=payload)
        update_model_fields(target=self, source=response)
        return response

    async def update_workspace_connections(
        self, connections: Union[DomainRouting, RoutingMap]
    ) -> Domain:
        payload = (
            connections.root if isinstance(connections, DomainRouting) else connections
        )
        response = await self.update_workspace_connections_op(data=payload)
        update_model_fields(target=self, source=response)
        return response

    async def verify_status(self) -> DomainVerificationStatus:
        response = await self.verify_domain_op()
        update_model_fields(target=self.domain_verification_status, source=response)
        return response

    async def delete(self) -> None:
        await self.delete_domain_op()
