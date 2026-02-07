import pytest
from typing import List

from codesphere import CodesphereSDK
from codesphere.resources.workspace import (
    Workspace,
    WorkspaceUpdate,
    WorkspaceStatus,
    CommandOutput,
)


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestWorkspacesIntegration:
    """Integration tests for workspace endpoints."""

    async def test_list_workspaces_by_team(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
        test_workspaces: List[Workspace],
    ):
        """Should retrieve a list of workspaces for a team."""
        workspaces = await sdk_client.workspaces.list(team_id=test_team_id)

        assert isinstance(workspaces, list)
        assert len(workspaces) >= len(test_workspaces)
        assert all(isinstance(ws, Workspace) for ws in workspaces)

        test_workspace_ids = {ws.id for ws in test_workspaces}
        listed_workspace_ids = {ws.id for ws in workspaces}
        assert test_workspace_ids.issubset(listed_workspace_ids)

    async def test_get_workspace_by_id(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should retrieve a specific workspace by ID."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        assert isinstance(workspace, Workspace)
        assert workspace.id == test_workspace.id
        assert workspace.name == test_workspace.name

    async def test_workspace_has_expected_fields(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Workspace should have all expected fields populated."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        assert workspace.id is not None
        assert workspace.team_id is not None
        assert workspace.name is not None
        assert workspace.plan_id is not None
        assert workspace.data_center_id is not None
        assert workspace.user_id is not None
        assert isinstance(workspace.is_private_repo, bool)
        assert isinstance(workspace.replicas, int)
        assert isinstance(workspace.restricted, bool)

    async def test_workspace_get_status(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should retrieve workspace status."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        status = await workspace.get_status()

        assert isinstance(status, WorkspaceStatus)
        assert isinstance(status.is_running, bool)

    async def test_workspace_execute_command(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should execute a command in the workspace."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        result = await workspace.execute_command(command="echo 'Hello from SDK test'")

        assert isinstance(result, CommandOutput)
        assert result.output is not None or result.error is not None

    async def test_workspace_execute_command_with_env(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should execute a command with custom environment variables."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        result = await workspace.execute_command(
            command="echo $TEST_CMD_VAR",
            env={"TEST_CMD_VAR": "sdk_test_value"},
        )

        assert isinstance(result, CommandOutput)

    async def test_workspace_env_vars_accessor(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Workspace model should provide access to env vars manager."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        env_vars_manager = workspace.env_vars
        assert env_vars_manager is not None


class TestWorkspaceUpdateOperations:
    """Integration tests for workspace update operations."""

    async def test_update_workspace_name(
        self,
        sdk_client: CodesphereSDK,
        test_workspaces: List[Workspace],
    ):
        """Should update an existing workspace's name."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspaces[1].id)
        original_name = workspace.name

        try:
            new_name = f"{original_name}-updated"
            update_data = WorkspaceUpdate(name=new_name)
            await workspace.update(data=update_data)

            assert workspace.name == new_name

            refreshed = await sdk_client.workspaces.get(workspace_id=workspace.id)
            assert refreshed.name == new_name
        finally:
            restore_data = WorkspaceUpdate(name=original_name)
            await workspace.update(data=restore_data)

    async def test_update_workspace_replicas(
        self,
        sdk_client: CodesphereSDK,
        test_workspaces: List[Workspace],
    ):
        """Should update workspace replica count."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspaces[1].id)
        original_replicas = workspace.replicas

        try:
            new_replicas = 1
            update_data = WorkspaceUpdate(replicas=new_replicas)
            await workspace.update(data=update_data)

            assert workspace.replicas == new_replicas
        finally:
            restore_data = WorkspaceUpdate(replicas=original_replicas)
            await workspace.update(data=restore_data)
