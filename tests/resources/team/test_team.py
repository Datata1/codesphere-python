import pytest

from codesphere.resources.team import Team, TeamCreate


class TestTeamsResource:
    """Tests for the TeamsResource class."""

    @pytest.mark.asyncio
    async def test_list_teams(self, teams_resource_factory, sample_team_list_data):
        """List teams should return a list of Team models."""
        resource, mock_client = teams_resource_factory(sample_team_list_data)

        result = await resource.list()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(team, Team) for team in result)

    @pytest.mark.asyncio
    async def test_list_teams_empty(self, teams_resource_factory):
        """List teams should handle empty response."""
        resource, _ = teams_resource_factory([])

        result = await resource.list()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_team_by_id(self, teams_resource_factory, sample_team_data):
        """Get team should return a single Team model."""
        resource, mock_client = teams_resource_factory(sample_team_data)

        result = await resource.get(team_id=12345)

        assert isinstance(result, Team)
        assert result.id == sample_team_data["id"]
        assert result.name == sample_team_data["name"]

    @pytest.mark.asyncio
    async def test_create_team(self, teams_resource_factory, sample_team_data):
        """Create team should return the created Team model."""
        resource, mock_client = teams_resource_factory(sample_team_data)
        payload = TeamCreate(name="New Team", dc=1)

        result = await resource.create(payload=payload)

        assert isinstance(result, Team)
        mock_client.request.assert_awaited_once()


class TestTeamModel:
    """Tests for the Team model and its methods."""

    @pytest.mark.asyncio
    async def test_delete_team(self, team_model_factory):
        """Team.delete() should call the delete operation."""
        team, mock_client = team_model_factory()

        await team.delete()

        mock_client.request.assert_awaited_once()

    def test_domains_raises_without_http_client(self, sample_team_data):
        """Accessing domains without valid HTTP client should raise RuntimeError."""
        team = Team.model_validate(sample_team_data)

        with pytest.raises(RuntimeError, match="detached model"):
            _ = team.domains


class TestTeamCreateSchema:
    """Tests for the TeamCreate schema."""

    def test_create_with_required_fields(self):
        """TeamCreate should be created with required fields."""
        create = TeamCreate(name="Test Team", dc=1)

        assert create.name == "Test Team"
        assert create.dc == 1

    def test_dump_to_camel_case(self):
        """TeamCreate should dump to camelCase for API requests."""
        create = TeamCreate(name="Test Team", dc=2)
        dumped = create.model_dump(by_alias=True)

        assert dumped["name"] == "Test Team"
        assert dumped["dc"] == 2
