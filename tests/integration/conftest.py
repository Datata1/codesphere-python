import logging
import os
import pytest
from typing import AsyncGenerator, List, Optional

from dotenv import load_dotenv

from codesphere import CodesphereSDK
from codesphere.resources.workspace import Workspace, WorkspaceCreate

load_dotenv()

TEST_WORKSPACE_PREFIX = "sdk-integration-test"

log = logging.getLogger(__name__)


def pytest_addoption(parser):
    """Add custom command line options for integration tests."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires valid API token)",
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires API token)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration is passed."""
    if config.getoption("--run-integration"):
        return

    skip_integration = pytest.mark.skip(
        reason="Need --run-integration option to run integration tests"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


@pytest.fixture(scope="session")
def integration_token() -> str:
    token = os.environ.get("CS_TOKEN")
    if not token:
        pytest.skip("CS_TOKEN environment variable not set")
    return token


@pytest.fixture(scope="session")
def integration_team_id() -> Optional[int]:
    team_id = os.environ.get("CS_TEST_TEAM_ID")
    return int(team_id) if team_id else None


@pytest.fixture(scope="session")
def integration_datacenter_id() -> int:
    dc_id = os.environ.get("CS_TEST_DC_ID", "1")
    return int(dc_id)


@pytest.fixture
async def sdk_client(integration_token) -> AsyncGenerator[CodesphereSDK, None]:
    sdk = CodesphereSDK()
    async with sdk:
        yield sdk


@pytest.fixture(scope="module")
async def module_sdk_client(integration_token) -> AsyncGenerator[CodesphereSDK, None]:
    sdk = CodesphereSDK()
    async with sdk:
        yield sdk


@pytest.fixture(scope="session")
async def session_sdk_client(integration_token) -> AsyncGenerator[CodesphereSDK, None]:
    sdk = CodesphereSDK()
    async with sdk:
        yield sdk


@pytest.fixture(scope="session")
async def test_team_id(
    session_sdk_client: CodesphereSDK,
    integration_team_id: Optional[int],
) -> int:
    if integration_team_id:
        return integration_team_id

    teams = await session_sdk_client.teams.list()
    if not teams:
        pytest.fail("No teams available for integration testing")
    return teams[0].id


@pytest.fixture(scope="session")
async def test_plan_id(session_sdk_client: CodesphereSDK) -> int:
    plans = await session_sdk_client.metadata.list_plans()

    micro_plan = next(
        (p for p in plans if p.title == "Micro" and not p.deprecated), None
    )
    if micro_plan:
        return micro_plan.id

    pytest.fail("No 'Micro' workspace plan available for testing")


@pytest.fixture(scope="session")
async def test_workspaces(
    session_sdk_client: CodesphereSDK,
    test_team_id: int,
    test_plan_id: int,
) -> AsyncGenerator[List[Workspace], None]:
    created_workspaces: List[Workspace] = []

    for i in range(2):
        workspace_name = f"{TEST_WORKSPACE_PREFIX}-{i + 1}"
        payload = WorkspaceCreate(
            team_id=test_team_id,
            name=workspace_name,
            plan_id=test_plan_id,
        )
        try:
            workspace = await session_sdk_client.workspaces.create(payload=payload)
            created_workspaces.append(workspace)
            log.info(f"Created test workspace: {workspace.name} (ID: {workspace.id})")
        except Exception as e:
            log.error(f"Failed to create test workspace {workspace_name}: {e}")
            for ws in created_workspaces:
                try:
                    await ws.delete()
                except Exception:
                    pass
            pytest.fail(f"Failed to create test workspaces: {e}")

    yield created_workspaces

    log.info("Cleaning up test workspaces")
    for workspace in created_workspaces:
        try:
            await workspace.delete()
            log.info(f"Deleted test workspace: {workspace.name} (ID: {workspace.id})")
        except Exception as e:
            log.warning(f"Failed to delete workspace {workspace.id}: {e}")


@pytest.fixture(scope="session")
async def test_workspace(test_workspaces: List[Workspace]) -> Workspace:
    return test_workspaces[0]
