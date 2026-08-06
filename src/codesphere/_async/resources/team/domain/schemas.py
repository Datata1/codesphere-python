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
    """A custom domain.

    Writes return the server's view of the domain and invalidate this
    instance: the returned object is authoritative for that moment, while
    ``self`` may have been overtaken by a concurrent write. Use the return
    value, or call :meth:`refresh`.
    """

    # A domain is keyed by name within its team, not by a numeric id.
    _identity_fields = ("name", "team_id")

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
        self._mark_stale()
        return response

    async def refresh(self, *, timeout: httpx.Timeout | float | None = None) -> Domain:
        """Re-read this domain from the server, in place."""
        from .operations import _GET_OP

        fresh = await self._execute(
            _GET_OP, team_id=self.team_id, name=self.name, timeout=timeout
        )
        self._adopt(fresh)
        return self

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
        self._mark_stale()
        return response

    async def verify_status(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> DomainVerificationStatus:
        from .operations import _VERIFY_OP

        response = await self._execute(
            _VERIFY_OP, team_id=self.team_id, name=self.name, timeout=timeout
        )
        # Triggers verification server-side, so this instance's nested
        # status can be overtaken the same way an update can.
        self._mark_stale()
        return response

    async def delete(self, *, timeout: httpx.Timeout | float | None = None) -> None:
        from .operations import _DELETE_OP

        await self._execute(
            _DELETE_OP, team_id=self.team_id, name=self.name, timeout=timeout
        )
