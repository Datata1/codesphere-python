from __future__ import annotations

from pydantic import Field, RootModel

from ....core.base import BoundModel, CamelModel
from ....utils import update_model_fields

type RoutingMap = dict[str, list[int]]


class CertificateRequestStatus(CamelModel):
    issued: bool
    reason: str | None = None


class DNSEntries(CamelModel):
    a: str
    cname: str
    txt: str


class DomainVerificationStatus(CamelModel):
    verified: bool
    reason: str | None = None


class CustomDomainConfig(CamelModel):
    restricted: bool | None = None
    max_body_size_mb: int | None = None
    max_connection_timeout_s: int | None = None
    use_regex: bool | None = None


class DomainRouting(RootModel):
    root: RoutingMap = Field(default_factory=dict)

    def add(self, path: str, workspace_ids: list[int]) -> DomainRouting:
        self.root[path] = workspace_ids
        return self


class DomainBase(CamelModel):
    name: str
    team_id: int
    data_center_id: int
    workspaces: RoutingMap
    certificate_request_status: CertificateRequestStatus
    dns_entries: DNSEntries
    domain_verification_status: DomainVerificationStatus
    custom_config_revision: int | None = None
    custom_config: CustomDomainConfig | None = None


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
