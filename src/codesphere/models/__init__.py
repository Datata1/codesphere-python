"""Shared request/response models (pure DTOs, no HTTP or async code).

Both the async and the sync client accept and return these classes, so
payloads built here work with either flavor.
"""

from .domain import (
    CertificateRequestStatus,
    CustomDomainConfig,
    DNSEntries,
    DomainBase,
    DomainRouting,
    DomainVerificationStatus,
    RoutingMap,
)
from .env_vars import EnvVar
from .git import GitHead
from .landscape import (
    PipelineStage,
    PipelineState,
    PipelineStatus,
    PipelineStatusList,
    Profile,
    ProfileBuilder,
    ProfileConfig,
)
from .logs import (
    LogEntry,
    LogKind,
    LogProblem,
    LogStage,
    LogTarget,
    ReplicaTarget,
    ServerTarget,
    StageTarget,
)
from .metadata import Characteristic, Datacenter, Image, WsPlan
from .team import TeamBase, TeamCreate
from .usage import LandscapeServiceEvent, LandscapeServiceSummary, ServiceAction
from .workspace import (
    CommandInput,
    CommandOutput,
    WorkspaceBase,
    WorkspaceCreate,
    WorkspaceStatus,
    WorkspaceUpdate,
)

__all__ = [
    "CertificateRequestStatus",
    "Characteristic",
    "CommandInput",
    "CommandOutput",
    "CustomDomainConfig",
    "DNSEntries",
    "Datacenter",
    "DomainBase",
    "DomainRouting",
    "DomainVerificationStatus",
    "EnvVar",
    "GitHead",
    "Image",
    "LandscapeServiceEvent",
    "LandscapeServiceSummary",
    "LogEntry",
    "LogKind",
    "LogProblem",
    "LogStage",
    "LogTarget",
    "PipelineStage",
    "PipelineState",
    "PipelineStatus",
    "PipelineStatusList",
    "Profile",
    "ProfileBuilder",
    "ProfileConfig",
    "ReplicaTarget",
    "RoutingMap",
    "ServerTarget",
    "ServiceAction",
    "StageTarget",
    "TeamBase",
    "TeamCreate",
    "WorkspaceBase",
    "WorkspaceCreate",
    "WorkspaceStatus",
    "WorkspaceUpdate",
    "WsPlan",
]
