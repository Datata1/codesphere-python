"""
Codesphere SDK - Python client for the Codesphere API.

This package provides a high-level asynchronous client for interacting
with the `Codesphere Public API <https://codesphere.com/api/swagger-ui/?ref=codesphere.ghost.io#/>`_.

Main Entrypoint:
    `from codesphere import CodesphereSDK`

Basic Usage:
    >>> import asyncio
    >>> from codesphere import CodesphereSDK
    >>>
    >>> async def main():
    >>>     async with CodesphereSDK() as sdk:
    >>>         teams = await sdk.teams.list()
    >>>         print(teams)
    >>>
    >>> asyncio.run(main())
"""

import logging

from .client import CodesphereSDK
from .config import RetryConfig
from .exceptions import (
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
    "AuthenticationError",
    "AuthorizationError",
    "Characteristic",
    # Exceptions
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
    "CategoryFlags",
    "Image",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "RetryConfig",
    # Resources
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
