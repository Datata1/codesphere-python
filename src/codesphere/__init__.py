"""
Codesphere SDK - Python client for the Codesphere API.

This package provides a high-level client for interacting with the
`Codesphere Public API <https://codesphere.com/api/swagger-ui/?ref=codesphere.ghost.io#/>`_,
in an async and a sync flavor with identical APIs.

Async (default):
    >>> import asyncio
    >>> from codesphere import CodesphereSDK
    >>>
    >>> async def main():
    >>>     async with CodesphereSDK() as sdk:
    >>>         teams = await sdk.teams.list()
    >>>         print(teams)
    >>>
    >>> asyncio.run(main())

Sync:
    >>> from codesphere.sync import CodesphereSDK
    >>>
    >>> with CodesphereSDK() as sdk:
    ...     teams = sdk.teams.list()
"""

import logging

from ._sync.client import CodesphereSDK as SyncCodesphereSDK
from .client import CodesphereSDK
from .client import CodesphereSDK as AsyncCodesphereSDK
from .config import RetryConfig
from .exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ClientStateError,
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
from .resources.flags import CategoryFlags, FlagCategory, FlagsSnapshot
from .resources.metadata import Characteristic, Datacenter, Image, WsPlan
from .resources.team import (
    CustomDomainConfig,
    Domain,
    DomainBase,
    DomainRouting,
    DomainVerificationStatus,
    Team,
    TeamBase,
    TeamCreate,
)
from .resources.workspace import (
    Workspace,
    WorkspaceCreate,
    WorkspaceStatus,
    WorkspaceUpdate,
)
from .resources.workspace.env_vars import EnvVar

logging.getLogger("codesphere").addHandler(logging.NullHandler())

__all__ = [
    "APIError",
    "AsyncCodesphereSDK",
    "AuthenticationError",
    "AuthorizationError",
    "CategoryFlags",
    "Characteristic",
    "ClientStateError",
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
    "FlagsSnapshot",
    "Image",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "RetryConfig",
    "SyncCodesphereSDK",
    "Team",
    "TeamBase",
    "TeamCreate",
    "TimeoutError",
    "ValidationError",
    "Workspace",
    "WorkspaceCreate",
    "WorkspaceStatus",
    "WorkspaceUpdate",
    "WsPlan",
]
