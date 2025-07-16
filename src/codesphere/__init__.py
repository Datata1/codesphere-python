# z.B. in src/codesphere/__init__.py oder einer eigenen client.py
from .client import APIHttpClient
from .resources.team.resource import TeamsResource


class CodesphereSDK:
    def __init__(self, token: str = None):
        self._http_client = APIHttpClient()
        # Die Ressourcen werden erst im __aenter__ initialisiert
        self.teams: TeamsResource | None = None

    async def __aenter__(self):
        """Wird beim Eintritt in den 'async with'-Block aufgerufen."""
        # Startet den internen HTTP-Client
        await self._http_client.__aenter__()

        # Initialisiert die Ressourcen-Handler mit dem aktiven Client
        self.teams = TeamsResource(self._http_client)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Wird beim Verlassen des 'async with'-Blocks aufgerufen."""
        # Schließt den internen HTTP-Client sicher
        await self._http_client.__aexit__(exc_type, exc_val, exc_tb)
