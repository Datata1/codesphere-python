from __future__ import annotations

from pydantic import Field, RootModel

from ..core.models import CamelModel

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
