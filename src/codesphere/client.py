"""
Codesphere SDK Client

This module provides the main client class, CodesphereSDK.
"""

from .http_client import APIHttpClient
from .resources.metadata import MetadataResource
from .resources.team import TeamsResource
from .resources.workspace import WorkspacesResource
from .resources.domain import DomainsResource


class CodesphereSDK:
    """The main entrypoint for interacting with the `Codesphere Public API <https://codesphere.com/api/swagger-ui/?ref=codesphere.ghost.io#/>`_.

    This class manages the HTTP client, its lifecycle,
    and provides access to the various API resources.

    Primary usage is via an asynchronous context manager:

    Usage:
        >>> import asyncio
        >>> from codesphere import CodesphereSDK
        >>>
        >>> async def main():
        >>>     async with CodesphereSDK() as sdk:
        >>>         teams = await sdk.teams.list()
        >>>         print(teams)
        >>>
        >>> asyncio.run(main())

    Attributes:
        teams (TeamsResource): Access to Team API operations.
        workspaces (WorkspacesResource): Access to Workspace API operations.
        metadata (MetadataResource): Access to Metadata API operations.
        domains (DomainResource): Access to Domain API operations.
    """

    teams: TeamsResource
    """Access to the Team API. (e.g., `sdk.teams.list()`)"""

    workspaces: WorkspacesResource
    """Access to the Workspace API. (e.g., `sdk.workspaces.list()`)"""

    metadata: MetadataResource
    """Access to the Metadata API. (e.g., `sdk.metadata.list_plans()`)"""

    domains: DomainsResource

    def __init__(self):
        self._http_client = APIHttpClient()
        self.teams = TeamsResource(self._http_client)
        self.workspaces = WorkspacesResource(self._http_client)
        self.metadata = MetadataResource(self._http_client)
        self.domains = DomainsResource(self._http_client)

    async def open(self):
        """Manually opens the underlying HTTP client session.

        Required for manual lifecycle control when not using `async with`.

        Usage:
            >>> sdk = CodesphereSDK()
            >>> await sdk.open()
            >>> # ... API calls ...
            >>> await sdk.close()
        """
        await self._http_client.open()

    async def close(self):
        """Manually closes the underlying HTTP client session."""
        await self._http_client.close()

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.close(exc_type, exc_val, exc_tb)
