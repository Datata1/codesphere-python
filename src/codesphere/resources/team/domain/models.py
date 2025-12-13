from __future__ import annotations
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ....core.handler import _APIOperationExecutor
from ....core.operations import APIOperation, AsyncCallable
from ....utils import update_model_fields
from ....http_client import APIHttpClient


log = logging.getLogger(__name__)

camel_config = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
)


class DomainBase(BaseModel):
    model_config = camel_config

    name: str
    team_id: int
    data_center_id: int
    workspaces: dict[str, list[int]]
    certificate_request_status: CertificateRequestStatus
    dns_entries: DNSEntries
    domain_verification_status: DomainVerificationStatus
    custom_config_revision: Optional[int] = None
    custom_config: Optional[CustomDomainConfig] = None


class CertificateRequestStatus(BaseModel):
    model_config = camel_config
    issued: bool
    reason: Optional[str] = None


class DNSEntries(BaseModel):
    model_config = camel_config
    a: str
    cname: str
    txt: str


class DomainVerificationStatus(BaseModel):
    model_config = camel_config
    verified: bool
    reason: Optional[str] = None


class CustomDomainConfig(BaseModel):
    model_config = camel_config
    restricted: Optional[bool] = None
    max_body_size_mb: Optional[int] = None
    max_connection_timeout_s: Optional[int] = None
    use_regex: Optional[bool] = None


class DomainRouting(BaseModel):
    """
    Helper class to build the routing configuration.
    Serializes to: {"/": [123], "/api": [456]}
    """

    root: Dict[str, List[int]] = Field(default_factory=dict)

    def add_route(self, path: str, workspace_ids: List[int]) -> DomainRouting:
        """Adds a routing rule."""
        self.root[path] = workspace_ids
        return self

    def to_dict(self) -> Dict[str, List[int]]:
        return self.root

    def model_dump(self, **kwargs) -> Dict[str, List[int]]:
        return self.root


class WorkspaceConnectionItem(BaseModel):
    model_config = camel_config
    path: str = Field(..., json_schema_extra={"is_dict_key": True})
    workspace_ids: List[int] = Field(..., json_schema_extra={"is_dict_value": True})


class Domain(DomainBase, _APIOperationExecutor):
    update_op: AsyncCallable[None] = Field(
        default=APIOperation(
            method="PATCH",
            endpoint_template="/domains/team/{team_id}/domain/{name}",
            response_model=DomainBase,
        ),
        exclude=True,
    )

    update_workspace_connections_op: AsyncCallable[None] = Field(
        default=APIOperation(
            method="PUT",
            endpoint_template="/domains/team/{team_id}/domain/{name}/workspace-connections",
            input_model=None,
            response_model=DomainBase,
        ),
        exclude=True,
    )

    verify_domain_op: AsyncCallable[None] = Field(
        default=APIOperation(
            method="POST",
            endpoint_template="/domains/team/{team_id}/domain/{name}/verify",
            response_model=DomainVerificationStatus,
        ),
        exclude=True,
    )

    delete_domain_op: AsyncCallable[None] = Field(
        default=APIOperation(
            method="DELETE",
            endpoint_template="/domains/team/{team_id}/domain/{name}",
            response_model=DomainBase,
        ),
        exclude=True,
    )

    async def update(self, data: CustomDomainConfig) -> DomainBase:
        payload = data.model_dump(exclude_unset=True, by_alias=True)
        response = await self.update_op(data=payload)
        update_model_fields(target=self, source=response)
        return response

    async def update_workspace_connections(
        self, connections: DomainRouting | Dict[str, List[int]]
    ) -> DomainBase:
        """
        Wandelt das Dict {"/": [123]} in eine Liste [{"path": "/", "workspaceIds": [123]}] um.
        """
        payload = connections
        if isinstance(connections, DomainRouting):
            payload = connections.to_dict()

        response = await self.update_workspace_connections_op(data=payload)
        update_model_fields(target=self, source=response)
        return response

    async def verify_status(self) -> DomainVerificationStatus:
        response = await self.verify_domain_op()
        update_model_fields(target=self.domain_verification_status, source=response)
        return response

    async def delete(self) -> None:
        await self.delete_domain_op()


class TeamDomainManager(_APIOperationExecutor):
    """
    Verwaltet Domains im Kontext eines spezifischen Teams.
    Zugriff typischerweise über 'team.domains'.
    """

    def __init__(self, http_client: APIHttpClient, team_id: int):
        self._http_client = http_client
        self.team_id = team_id

    list_op: AsyncCallable[List[Domain]] = Field(
        default=APIOperation(
            method="GET",
            endpoint_template="/domains/team/{team_id}",
            response_model=List[Domain],
        ),
        exclude=True,
    )

    get_op: AsyncCallable[Domain] = Field(
        default=APIOperation(
            method="GET",
            endpoint_template="/domains/team/{team_id}/domain/{domain_name}",
            response_model=Domain,
        ),
        exclude=True,
    )

    create_op: AsyncCallable[Domain] = Field(
        default=APIOperation(
            method="POST",
            endpoint_template="/domains/team/{team_id}/domain/{domain_name}",
            response_model=Domain,
        ),
        exclude=True,
    )

    update_op: AsyncCallable[Domain] = Field(
        default=APIOperation(
            method="PATCH",
            endpoint_template="/domains/team/{team_id}/domain/{domain_name}",
            input_model=CustomDomainConfig,
            response_model=Domain,
        ),
        exclude=True,
    )

    update_ws_op: AsyncCallable[Domain] = Field(
        default=APIOperation(
            method="PUT",
            endpoint_template="/domains/team/{team_id}/domain/{domain_name}/workspace-connections",
            input_model=None,
            response_model=Domain,
        ),
        exclude=True,
    )

    async def list(self) -> List[Domain]:
        """
        Listet alle Domains dieses Teams auf.
        """
        return await self.list_op()

    async def get(self, domain_name: str) -> Domain:
        """
        Holt eine spezifische Domain dieses Teams.
        """
        return await self.get_op(domain_name=domain_name)

    async def create(self, domain_name: str) -> Domain:
        """
        Registriert eine neue Domain für dieses Team.
        """
        return await self.create_op(domain_name=domain_name)

    async def update(self, domain_name: str, config: CustomDomainConfig) -> Domain:
        """
        Aktualisiert die Konfiguration einer Domain, ohne sie vorher laden zu müssen.

        Args:
            domain_name (str): Der Name der Domain (z.B. "example.com")
            config (CustomDomainConfig): Die neuen Einstellungen.
        """
        return await self.update_op(domain_name=domain_name, data=config)

    async def update_workspace_connections(
        self, domain_name: str, connections: DomainRouting | Dict[str, List[int]]
    ) -> Domain:
        payload = connections
        if isinstance(connections, DomainRouting):
            payload = connections.to_dict()

        return await self.update_ws_op(domain_name=domain_name, data=payload)
