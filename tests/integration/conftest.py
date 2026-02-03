"""
Shared fixtures for integration tests.

These fixtures provide real SDK clients configured for integration testing.
Set the CS_TOKEN environment variable before running.
"""

import os
import pytest
from typing import AsyncGenerator, List, Optional

from dotenv import load_dotenv

from codesphere import CodesphereSDK
from codesphere.resources.workspace import Workspace, WorkspaceCreate

# Load .env file for local development
load_dotenv()

# Constants for test workspaces
TEST_WORKSPACE_PREFIX = "sdk-integration-test"


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
    """
    Get the API token for integration tests.

    Reads from CS_TOKEN environment variable.
    """
    token = os.environ.get("CS_TOKEN")
    if not token:
        pytest.skip("CS_TOKEN environment variable not set")
    return token


@pytest.fixture(scope="session")
def integration_team_id() -> Optional[int]:
    """
    Get an optional team ID for integration tests.

    Reads from CS_TEST_TEAM_ID environment variable.
    If not set, tests will use the first available team.
    """
    team_id = os.environ.get("CS_TEST_TEAM_ID")
    return int(team_id) if team_id else None


@pytest.fixture(scope="session")
def integration_datacenter_id() -> int:
    """
    Get the datacenter ID for integration tests.

    Reads from CS_TEST_DC_ID environment variable.
    Defaults to 1 if not set.
    """
    dc_id = os.environ.get("CS_TEST_DC_ID", "1")
    return int(dc_id)


@pytest.fixture
async def sdk_client(integration_token) -> AsyncGenerator[CodesphereSDK, None]:
    """
    Provide a configured SDK client for integration tests.

    The client is automatically opened and closed.
    """
    sdk = CodesphereSDK()
    async with sdk:
        yield sdk


@pytest.fixture(scope="module")
async def module_sdk_client(integration_token) -> AsyncGenerator[CodesphereSDK, None]:
    """
    Provide a module-scoped SDK client for integration tests.

    Use this for tests that need to share state within a module.
    """
    sdk = CodesphereSDK()
    async with sdk:
        yield sdk


@pytest.fixture(scope="session")
async def session_sdk_client(integration_token) -> AsyncGenerator[CodesphereSDK, None]:
    """
    Provide a session-scoped SDK client for integration tests.

    Used for creating/deleting test workspaces that persist across all tests.
    """
    sdk = CodesphereSDK()
    async with sdk:
        yield sdk


@pytest.fixture(scope="session")
async def test_team_id(
    session_sdk_client: CodesphereSDK,
    integration_team_id: Optional[int],
) -> int:
    """
    Get the team ID to use for integration tests.

    Uses CS_TEST_TEAM_ID if set, otherwise uses the first available team.
    """
    if integration_team_id:
        return integration_team_id

    teams = await session_sdk_client.teams.list()
    if not teams:
        pytest.fail("No teams available for integration testing")
    return teams[0].id


@pytest.fixture(scope="session")
async def test_plan_id(session_sdk_client: CodesphereSDK) -> int:
    """
    Get a valid plan ID for creating test workspaces.

    Uses plan ID 8 (Micro) which is suitable for testing.
    Falls back to first non-deprecated plan if not available.
    """
    plans = await session_sdk_client.metadata.list_plans()

    # Prefer plan ID 8 (Micro) for testing
    micro_plan = next((p for p in plans if p.id == 8 and not p.deprecated), None)
    if micro_plan:
        return micro_plan.id

    # Fallback to first non-deprecated, non-free plan
    active_plans = [p for p in plans if not p.deprecated and p.id != 1]
    if active_plans:
        return active_plans[0].id

    # Last resort: any plan
    if plans:
        return plans[0].id

    pytest.fail("No workspace plans available")


@pytest.fixture(scope="session")
async def test_workspaces(
    session_sdk_client: CodesphereSDK,
    test_team_id: int,
    test_plan_id: int,
) -> AsyncGenerator[List[Workspace], None]:
    """
    Create test workspaces for integration tests.

    Creates 2 workspaces at the start of the test session and deletes them
    after all tests complete. This fixture ensures workspace-dependent tests
    have resources to work with.
    """
    created_workspaces: List[Workspace] = []

    # Create test workspaces
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
            print(f"\n✓ Created test workspace: {workspace.name} (ID: {workspace.id})")
        except Exception as e:
            print(f"\n✗ Failed to create test workspace {workspace_name}: {e}")
            # Clean up any workspaces we did create
            for ws in created_workspaces:
                try:
                    await ws.delete()
                except Exception:
                    pass
            pytest.fail(f"Failed to create test workspaces: {e}")

    yield created_workspaces

    # Cleanup: delete test workspaces
    print("\n--- Cleaning up test workspaces ---")
    for workspace in created_workspaces:
        try:
            await workspace.delete()
            print(f"✓ Deleted test workspace: {workspace.name} (ID: {workspace.id})")
        except Exception as e:
            print(f"✗ Failed to delete workspace {workspace.id}: {e}")


@pytest.fixture(scope="session")
async def test_workspace(test_workspaces: List[Workspace]) -> Workspace:
    """
    Provide a single test workspace for tests that only need one.
    """
    return test_workspaces[0]
