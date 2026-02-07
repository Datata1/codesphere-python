import pytest
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx


class MockResponseFactory:
    """Factory for creating mock HTTP responses."""

    @staticmethod
    def create(
        status_code: int = 200,
        json_data: Optional[Any] = None,
        raise_for_status: bool = False,
    ) -> AsyncMock:
        """Create a mock httpx.Response."""
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data if json_data is not None else {}

        if raise_for_status or 400 <= status_code < 600:
            mock_request = MagicMock(spec=httpx.Request)
            mock_request.method = "GET"
            mock_request.url = "https://test.com/test-endpoint"

            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"{status_code} Error",
                request=mock_request,
                response=mock_response,
            )
        else:
            mock_response.raise_for_status.return_value = None

        return mock_response


class MockHTTPClientFactory:
    """Factory for creating mock HTTP clients."""

    @staticmethod
    def create(
        response: Optional[AsyncMock] = None,
        status_code: int = 200,
        json_data: Optional[Any] = None,
    ) -> AsyncMock:
        """Create a mock httpx.AsyncClient."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        if response is None:
            response = MockResponseFactory.create(
                status_code=status_code, json_data=json_data
            )

        mock_client.request.return_value = response
        return mock_client


@pytest.fixture
def mock_response_factory():
    return MockResponseFactory


@pytest.fixture
def mock_http_client_factory():
    return MockHTTPClientFactory


@pytest.fixture
def mock_http_response():
    return MockResponseFactory.create(status_code=200, json_data={})


@pytest.fixture
def mock_async_client(mock_http_response):
    return MockHTTPClientFactory.create(response=mock_http_response)


@pytest.fixture
def mock_token():
    return "test-api-token-12345"


@pytest.fixture
def mock_settings(mock_token):
    from pydantic import SecretStr

    mock = MagicMock()
    mock.token = SecretStr(mock_token)
    mock.base_url = "https://codesphere.com/api"
    mock.client_timeout_connect = 10.0
    mock.client_timeout_read = 30.0
    return mock


@pytest.fixture
def api_http_client(mock_settings):
    with patch("codesphere.http_client.settings", mock_settings):
        from codesphere.http_client import APIHttpClient

        client = APIHttpClient()
        yield client


@pytest.fixture
def sdk_client(mock_settings):
    with patch("codesphere.http_client.settings", mock_settings):
        from codesphere.client import CodesphereSDK

        sdk = CodesphereSDK()
        yield sdk


@pytest.fixture
def mock_http_client_for_resource(mock_response_factory):
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
def sample_team_data():
    return {
        "id": 12345,
        "name": "Test Team",
        "description": "A test team",
        "avatarId": None,
        "avatarUrl": None,
        "isFirst": True,
        "defaultDataCenterId": 1,
        "role": 1,
    }


@pytest.fixture
def sample_team_list_data(sample_team_data):
    return [
        sample_team_data,
        {
            "id": 12346,
            "name": "Test Team 2",
            "description": "Another test team",
            "avatarId": None,
            "avatarUrl": None,
            "isFirst": False,
            "defaultDataCenterId": 2,
            "role": 2,
        },
    ]


@pytest.fixture
def sample_workspace_data():
    return {
        "id": 72678,
        "teamId": 12345,
        "name": "test-workspace",
        "planId": 8,
        "isPrivateRepo": True,
        "replicas": 1,
        "baseImage": "ubuntu:22.04",
        "dataCenterId": 1,
        "userId": 100,
        "gitUrl": None,
        "initialBranch": None,
        "sourceWorkspaceId": None,
        "welcomeMessage": None,
        "vpnConfig": None,
        "restricted": False,
    }


@pytest.fixture
def sample_workspace_list_data(sample_workspace_data):
    return [
        sample_workspace_data,
        {**sample_workspace_data, "id": 72679, "name": "test-workspace-2"},
    ]


@pytest.fixture
def sample_domain_data():
    return {
        "name": "test.example.com",
        "teamId": 12345,
        "dataCenterId": 1,
        "workspaces": {"/": [72678]},
        "certificateRequestStatus": {"issued": True, "reason": None},
        "dnsEntries": {
            "a": "192.168.1.1",
            "cname": "proxy.codesphere.com",
            "txt": "verification-token",
        },
        "domainVerificationStatus": {"verified": True, "reason": None},
        "customConfigRevision": None,
        "customConfig": None,
    }


@pytest.fixture
def sample_env_var_data():
    return [
        {"name": "API_KEY", "value": "secret123"},
        {"name": "DEBUG", "value": "true"},
    ]


@pytest.fixture
def teams_resource_factory(mock_http_client_for_resource):
    def _create(response_data: Any):
        from codesphere.resources.team import TeamsResource

        mock_client = mock_http_client_for_resource(response_data)
        resource = TeamsResource(http_client=mock_client)
        return resource, mock_client

    return _create


@pytest.fixture
def workspaces_resource_factory(mock_http_client_for_resource):
    def _create(response_data: Any):
        from codesphere.resources.workspace import WorkspacesResource

        mock_client = mock_http_client_for_resource(response_data)
        resource = WorkspacesResource(http_client=mock_client)
        return resource, mock_client

    return _create


@pytest.fixture
def metadata_resource_factory(mock_http_client_for_resource):
    def _create(response_data: Any):
        from codesphere.resources.metadata import MetadataResource

        mock_client = mock_http_client_for_resource(response_data)
        resource = MetadataResource(http_client=mock_client)
        return resource, mock_client

    return _create


@pytest.fixture
def team_model_factory(mock_http_client_for_resource, sample_team_data):
    def _create(response_data: Any = None, team_data: dict = None):
        from codesphere.resources.team import Team

        data = team_data or sample_team_data
        mock_client = mock_http_client_for_resource(
            response_data if response_data is not None else {}
        )
        team = Team.model_validate(data)
        team._http_client = mock_client
        return team, mock_client

    return _create


@pytest.fixture
def workspace_model_factory(mock_http_client_for_resource, sample_workspace_data):
    def _create(response_data: Any = None, workspace_data: dict = None):
        from codesphere.resources.workspace import Workspace

        data = workspace_data or sample_workspace_data
        mock_client = mock_http_client_for_resource(
            response_data if response_data is not None else {}
        )
        workspace = Workspace.model_validate(data)
        workspace._http_client = mock_client
        return workspace, mock_client

    return _create


@pytest.fixture
def domain_model_factory(mock_http_client_for_resource, sample_domain_data):
    def _create(response_data: Any = None, domain_data: dict = None):
        from codesphere.resources.team.domain.resources import Domain

        data = domain_data or sample_domain_data
        mock_client = mock_http_client_for_resource(
            response_data if response_data is not None else {}
        )
        domain = Domain.model_validate(data)
        domain._http_client = mock_client
        return domain, mock_client

    return _create
