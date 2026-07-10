from __future__ import annotations

import logging

from ....core.base import BoundModel
from ....utils import update_model_fields
from .schemas import (
    CustomDomainConfig,
    DomainBase,
    DomainRouting,
    DomainVerificationStatus,
    RoutingMap,
)

log = logging.getLogger(__name__)


class Domain(DomainBase, BoundModel):
    async def update(self, data: CustomDomainConfig) -> Domain:
        from .operations import _UPDATE_OP

        response = await self._execute(
            _UPDATE_OP, team_id=self.team_id, name=self.name, data=data
        )
        update_model_fields(target=self, source=response)
        return response

    async def update_workspace_connections(
        self, connections: DomainRouting | RoutingMap
    ) -> Domain:
        from .operations import _UPDATE_WS_OP

        payload = (
            connections.root if isinstance(connections, DomainRouting) else connections
        )
        response = await self._execute(
            _UPDATE_WS_OP, team_id=self.team_id, name=self.name, data=payload
        )
        update_model_fields(target=self, source=response)
        return response

    async def verify_status(self) -> DomainVerificationStatus:
        from .operations import _VERIFY_OP

        response = await self._execute(_VERIFY_OP, team_id=self.team_id, name=self.name)
        update_model_fields(target=self.domain_verification_status, source=response)
        return response

    async def delete(self) -> None:
        from .operations import _DELETE_OP

        await self._execute(_DELETE_OP, team_id=self.team_id, name=self.name)
