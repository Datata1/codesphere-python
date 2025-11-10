"""
Pydantic models for the Domain resource.
"""

from __future__ import annotations
import logging
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from ...utils import update_model_fields
from ...core import _APIOperationExecutor, APIOperation, AsyncCallable

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
    max_body_size_mb: int
    max_connection_timeout: int
    use_regex: bool
    restricted: bool


class Domain(DomainBase, _APIOperationExecutor):
    update_domain_op: AsyncCallable[None] = Field(
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

    async def update_domain(self, data: CustomDomainConfig) -> DomainBase:
        await self.update_domain_op(data=data)
        update_model_fields(target=self.custom_config, source=data)

    async def update_workspace_connections(
        self, data: dict[str, list[int]]
    ) -> DomainBase:
        response = await self.update_workspace_connections_op(data=data)
        update_model_fields(target=self, source=response)

    async def verify_status(self) -> DomainVerificationStatus:
        response = await self.verify_domain_op()
        update_model_fields(target=self.domain_verification_status, source=response)
        return response

    async def delete(self) -> None:
        await self.delete_domain_op()
