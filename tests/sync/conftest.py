import pytest
import respx

from codesphere import RetryConfig
from codesphere.sync import CodesphereSDK

SYNC_BASE_URL = "https://sync.test/api"


@pytest.fixture
def mock_api():
    with respx.mock(base_url=SYNC_BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
def sdk(mock_api):
    """An opened sync CodesphereSDK wired to the respx-mocked transport.

    Retries off so error-path tests stay single-shot; retry behavior has
    its own tests.
    """
    with CodesphereSDK(
        token="test-token",
        base_url=SYNC_BASE_URL,
        retry=RetryConfig(max_retries=0),
    ) as client:
        yield client


@pytest.fixture
def sample_workspace_json():
    return {
        "id": 5,
        "teamId": 1,
        "name": "ws",
        "planId": 8,
        "isPrivateRepo": True,
        "replicas": 1,
        "dataCenterId": 1,
        "userId": 1,
        "restricted": False,
    }


@pytest.fixture
def sample_team_json():
    return {
        "id": 1,
        "name": "Team",
        "description": None,
        "avatarId": None,
        "avatarUrl": None,
        "isFirst": True,
        "defaultDataCenterId": 1,
        "role": 1,
    }
