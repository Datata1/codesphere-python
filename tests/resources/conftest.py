import pytest
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock


class ResourceTestHelper:
    """
    Helper class for resource tests providing common assertion patterns.

    Usage:
        helper = ResourceTestHelper(mock_client, "GET", "/teams")
        await resource.list()
        helper.assert_called()
    """

    def __init__(
        self,
        mock_client: AsyncMock,
        expected_method: str,
        expected_endpoint: str,
    ):
        self.mock_client = mock_client
        self.expected_method = expected_method
        self.expected_endpoint = expected_endpoint

    def assert_called(self, json_payload: Any = None) -> None:
        """Assert the HTTP request was made with expected parameters."""
        self.mock_client.request.assert_awaited()
        call_args = self.mock_client.request.call_args

        assert call_args.kwargs.get("method") == self.expected_method
        assert call_args.kwargs.get("endpoint") == self.expected_endpoint

        if json_payload is not None:
            assert call_args.kwargs.get("json") == json_payload


@pytest.fixture
def resource_test_helper():
    """Provide the ResourceTestHelper class for resource tests."""
    return ResourceTestHelper


@pytest.fixture
def mock_http_client_for_resource(mock_response_factory):
    """
    Create a configurable mock HTTP client for resource testing.

    Returns a factory function that creates configured mock clients.
    """

    def _create(response_data: Any, status_code: int = 200) -> MagicMock:
        mock_client = MagicMock()
        mock_response = mock_response_factory.create(
            status_code=status_code,
            json_data=response_data,
        )
        mock_client.request = AsyncMock(return_value=mock_response)
        return mock_client

    return _create


@pytest.fixture
def teams_resource_factory(mock_http_client_for_resource):
    """Factory for creating TeamsResource instances with mock data."""

    def _create(response_data: Any):
        from codesphere.resources.team import TeamsResource

        mock_client = mock_http_client_for_resource(response_data)
        resource = TeamsResource(http_client=mock_client)
        return resource, mock_client

    return _create


@pytest.fixture
def workspaces_resource_factory(mock_http_client_for_resource):
    """Factory for creating WorkspacesResource instances with mock data."""

    def _create(response_data: Any):
        from codesphere.resources.workspace import WorkspacesResource

        mock_client = mock_http_client_for_resource(response_data)
        resource = WorkspacesResource(http_client=mock_client)
        return resource, mock_client

    return _create


@pytest.fixture
def metadata_resource_factory(mock_http_client_for_resource):
    """Factory for creating MetadataResource instances with mock data."""

    def _create(response_data: Any):
        from codesphere.resources.metadata import MetadataResource

        mock_client = mock_http_client_for_resource(response_data)
        resource = MetadataResource(http_client=mock_client)
        return resource, mock_client

    return _create


@pytest.fixture
def team_model_factory(mock_http_client_for_resource, sample_team_data):
    """Factory for creating Team model instances with mock HTTP client."""

    def _create(response_data: Any = None, team_data: Dict = None):
        from codesphere.resources.team import Team

        data = team_data or sample_team_data
        mock_client = mock_http_client_for_resource(response_data or {})
        team = Team.model_validate(data)
        team._http_client = mock_client
        return team, mock_client

    return _create


@pytest.fixture
def workspace_model_factory(mock_http_client_for_resource, sample_workspace_data):
    """Factory for creating Workspace model instances with mock HTTP client."""

    def _create(response_data: Any = None, workspace_data: Dict = None):
        from codesphere.resources.workspace import Workspace

        data = workspace_data or sample_workspace_data
        mock_client = mock_http_client_for_resource(response_data or {})
        workspace = Workspace.model_validate(data)
        workspace._http_client = mock_client
        return workspace, mock_client

    return _create


@pytest.fixture
def domain_model_factory(mock_http_client_for_resource, sample_domain_data):
    """Factory for creating Domain model instances with mock HTTP client."""

    def _create(response_data: Any = None, domain_data: Dict = None):
        from codesphere.resources.team.domain.resources import Domain

        data = domain_data or sample_domain_data
        mock_client = mock_http_client_for_resource(response_data or {})
        domain = Domain.model_validate(data)
        domain._http_client = mock_client
        return domain, mock_client

    return _create
