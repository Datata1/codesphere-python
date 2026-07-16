"""Synchronous Codesphere client.

Mirrors the async API with identical signatures, minus ``async``/``await``:

    >>> from codesphere.sync import CodesphereSDK
    >>>
    >>> with CodesphereSDK() as sdk:
    ...     teams = sdk.teams.list()

The implementation is generated from the async source
(``codesphere._async``) — see ``make sync-gen``. Request/response models
are shared between both flavors (``codesphere.models``); only entities
with API methods (``Workspace``, ``Team``, ``Domain``, ``LogStream``)
exist per flavor.
"""

from codesphere._sync.client import CodesphereSDK
from codesphere._sync.resources.flags import FlagsResource
from codesphere._sync.resources.metadata import MetadataResource
from codesphere._sync.resources.team import Team, TeamsResource
from codesphere._sync.resources.team.domain import TeamDomainManager
from codesphere._sync.resources.team.domain.schemas import Domain
from codesphere._sync.resources.team.usage import TeamUsageManager
from codesphere._sync.resources.workspace import (
    LogStream,
    Workspace,
    WorkspacesResource,
)
from codesphere.config import RetryConfig
from codesphere.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    CodesphereError,
    ConflictError,
    FeatureFlagError,
    FeatureNotAvailableError,
    FeatureNotEnabledError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from codesphere.feature_flags import CategoryFlags, FlagCategory, FlagsSnapshot
from codesphere.models import (
    Characteristic,
    CustomDomainConfig,
    Datacenter,
    DomainBase,
    DomainRouting,
    DomainVerificationStatus,
    EnvVar,
    Image,
    TeamBase,
    TeamCreate,
    WorkspaceCreate,
    WorkspaceStatus,
    WorkspaceUpdate,
    WsPlan,
)

__all__ = [
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "CategoryFlags",
    "Characteristic",
    "CodesphereError",
    "CodesphereSDK",
    "ConflictError",
    "CustomDomainConfig",
    "Datacenter",
    "Domain",
    "DomainBase",
    "DomainRouting",
    "DomainVerificationStatus",
    "EnvVar",
    "FeatureFlagError",
    "FeatureNotAvailableError",
    "FeatureNotEnabledError",
    "FlagCategory",
    "FlagsResource",
    "FlagsSnapshot",
    "Image",
    "LogStream",
    "MetadataResource",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "RetryConfig",
    "Team",
    "TeamBase",
    "TeamCreate",
    "TeamDomainManager",
    "TeamUsageManager",
    "TeamsResource",
    "TimeoutError",
    "ValidationError",
    "Workspace",
    "WorkspaceCreate",
    "WorkspaceStatus",
    "WorkspaceUpdate",
    "WorkspacesResource",
    "WsPlan",
]
