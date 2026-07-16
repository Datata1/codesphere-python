from __future__ import annotations

import httpx

from codesphere.models.domain import (
    CertificateRequestStatus,
    CustomDomainConfig,
    DNSEntries,
    DomainBase,
    DomainRouting,
    DomainVerificationStatus,
    RoutingMap,
)
from codesphere.utils import update_model_fields

from ....core.base import BoundModel

__all__ = [
    "CertificateRequestStatus",
    "CustomDomainConfig",
    "DNSEntries",
    "Domain",
    "DomainBase",
    "DomainRouting",
    "DomainVerificationStatus",
    "RoutingMap",
]


class Domain(DomainBase, BoundModel):
    async def update(
        self,
        data: CustomDomainConfig,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> Domain:
        from .operations import _UPDATE_OP

        response = await self._execute(
            _UPDATE_OP, team_id=self.team_id, name=self.name, data=data, timeout=timeout
        )
        update_model_fields(target=self, source=response)
        return response

    async def update_workspace_connections(
        self,
        connections: DomainRouting | RoutingMap,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> Domain:
        from .operations import _UPDATE_WS_OP

        payload = (
            connections.root if isinstance(connections, DomainRouting) else connections
        )
        response = await self._execute(
            _UPDATE_WS_OP,
            team_id=self.team_id,
            name=self.name,
            data=payload,
            timeout=timeout,
        )
        update_model_fields(target=self, source=response)
        return response

    async def verify_status(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> DomainVerificationStatus:
        from .operations import _VERIFY_OP

        response = await self._execute(
            _VERIFY_OP, team_id=self.team_id, name=self.name, timeout=timeout
        )
        update_model_fields(target=self.domain_verification_status, source=response)
        return response

    async def delete(self, *, timeout: httpx.Timeout | float | None = None) -> None:
        from .operations import _DELETE_OP

        await self._execute(
            _DELETE_OP, team_id=self.team_id, name=self.name, timeout=timeout
        )
