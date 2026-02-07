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
from .exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    CodesphereError,
    ConflictError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
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
from .resources.workspace.envVars import EnvVar

logging.getLogger("codesphere").addHandler(logging.NullHandler())

__all__ = [
    "CodesphereSDK",
    # Exceptions
    "CodesphereError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "RateLimitError",
    "APIError",
    "NetworkError",
    "TimeoutError",
    # Resources
    "Team",
    "TeamCreate",
    "TeamBase",
    "Workspace",
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceStatus",
    "EnvVar",
    "Datacenter",
    "Characteristic",
    "WsPlan",
    "Image",
    "Domain",
    "CustomDomainConfig",
    "DomainVerificationStatus",
    "DomainBase",
    "DomainRouting",
]
