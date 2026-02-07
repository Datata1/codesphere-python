import pytest


@pytest.mark.integration
class TestListClientInjection:
    """Verify that items returned from list operations have working _http_client."""

    @pytest.mark.asyncio
    async def test_workspaces_list_items_can_use_instance_methods(
        self, sdk_client, test_team_id
    ):
        """Workspaces from list() should be able to call instance methods."""
        workspaces = await sdk_client.workspaces.list(team_id=test_team_id)

        if len(workspaces) == 0:
            pytest.skip("No workspaces available for testing")

        workspace = workspaces[0]

        assert workspace._http_client is not None

        status = await workspace.get_status()
        assert status is not None

    @pytest.mark.asyncio
    async def test_teams_list_items_can_access_sub_resources(self, sdk_client):
        """Teams from list() should be able to access sub-resources."""
        teams = await sdk_client.teams.list()

        if len(teams) == 0:
            pytest.skip("No teams available for testing")

        team = teams[0]

        assert team._http_client is not None

        domains_manager = team.domains
        assert domains_manager is not None
