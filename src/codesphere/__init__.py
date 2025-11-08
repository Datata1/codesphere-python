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

from .exceptions import CodesphereError, AuthenticationError
from .resources.team import Team, TeamCreate, TeamBase
from .resources.workspace import (
    Workspace,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceStatus,
)
from .resources.metadata import Datacenter, Characteristic, WsPlan, Image

logging.getLogger("codesphere").addHandler(logging.NullHandler())

__all__ = [
    "CodesphereSDK",
    "CodesphereError",
    "AuthenticationError",
    "Team",
    "TeamCreate",
    "TeamBase",
    "Workspace",
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceStatus",
    "Datacenter",
    "Characteristic",
    "WsPlan",
    "Image",
]
