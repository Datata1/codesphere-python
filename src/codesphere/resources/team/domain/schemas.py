from __future__ import annotations

from typing import Dict, List, Optional, TypeAlias

from pydantic import Field, RootModel

from ....core.base import CamelModel

RoutingMap: TypeAlias = Dict[str, List[int]]


class CertificateRequestStatus(CamelModel):
    issued: bool
    reason: Optional[str] = None


class DNSEntries(CamelModel):
    a: str
    cname: str
    txt: str


class DomainVerificationStatus(CamelModel):
    verified: bool
    reason: Optional[str] = None


class CustomDomainConfig(CamelModel):
    restricted: Optional[bool] = None
    max_body_size_mb: Optional[int] = None
    max_connection_timeout_s: Optional[int] = None
    use_regex: Optional[bool] = None


class DomainRouting(RootModel):
    root: RoutingMap = Field(default_factory=dict)

    def add(self, path: str, workspace_ids: List[int]) -> DomainRouting:
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
    custom_config_revision: Optional[int] = None
    custom_config: Optional[CustomDomainConfig] = None
