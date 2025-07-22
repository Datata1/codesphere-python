# z.B. in src/codesphere/__init__.py oder einer eigenen client.py
from .client import APIHttpClient
from .resources.team.resources import TeamsResource
from .resources.workspace.resources import WorkspacesResource
from .resources.metadata.resources import MetadataResource
from .resources.workspace.models import (
    Workspace,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceStatus,
)


class CodesphereSDK:
    def __init__(self, token: str = None):
        self._http_client = APIHttpClient()
        self.teams: TeamsResource | None = None
        self.workspaces: WorkspacesResource | None = None

    async def __aenter__(self):
        """Wird beim Eintritt in den 'async with'-Block aufgerufen."""
        await self._http_client.__aenter__()

        self.teams = TeamsResource(self._http_client)
        self.workspaces = WorkspacesResource(self._http_client)
        self.metadata = MetadataResource(self._http_client)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Wird beim Verlassen des 'async with'-Blocks aufgerufen."""
        await self._http_client.__aexit__(exc_type, exc_val, exc_tb)


__all__ = [
    "CodesphereSDK",
    "CodesphereError",
    "AuthenticationError",
    "Team",
    "TeamCreate",
    "TeamInList",
    "Workspace",
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceStatus",
]
