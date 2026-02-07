import pytest

from codesphere import CodesphereSDK
from codesphere.resources.team import Team


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestTeamsIntegration:
    """Integration tests for team endpoints."""

    async def test_list_teams(self, sdk_client: CodesphereSDK):
        """Should retrieve a list of teams for the authenticated user."""
        teams = await sdk_client.teams.list()

        assert isinstance(teams, list)
        assert len(teams) > 0
        assert all(isinstance(team, Team) for team in teams)

        first_team = teams[0]
        assert first_team.id is not None
        assert first_team.name is not None

    async def test_get_team_by_id(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        """Should retrieve a specific team by ID."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        assert isinstance(team, Team)
        assert team.id == test_team_id

    async def test_team_has_domains_accessor(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        """Team model should provide access to domains manager."""
        team = await sdk_client.teams.get(team_id=test_team_id)

        domains_manager = team.domains
        assert domains_manager is not None
