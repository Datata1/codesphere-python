from .http_client import APIHttpClient
from .resources.metadata import MetadataResource
from .resources.team import TeamsResource
from .resources.workspace import WorkspacesResource


class CodesphereSDK:
    teams: TeamsResource
    workspaces: WorkspacesResource
    metadata: MetadataResource

    def __init__(self):
        self._http_client = APIHttpClient()
        self.teams = TeamsResource(self._http_client)
        self.workspaces = WorkspacesResource(self._http_client)
        self.metadata = MetadataResource(self._http_client)

    async def open(self):
        await self._http_client.open()

    async def close(self):
        await self._http_client.close()

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.close(exc_type, exc_val, exc_tb)
