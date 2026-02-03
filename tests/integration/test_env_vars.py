"""
Integration tests for Workspace Environment Variables.

These tests verify CRUD operations for environment variables on workspaces.
"""

import pytest

from codesphere import CodesphereSDK
from codesphere.resources.workspace import Workspace


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestEnvVarsIntegration:
    """Integration tests for workspace environment variables."""

    async def test_get_env_vars_empty(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should retrieve environment variables (may be empty initially)."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        env_vars = await workspace.env_vars.get()

        # ResourceList is iterable and has length
        assert hasattr(env_vars, "__iter__")
        assert hasattr(env_vars, "__len__")
        assert len(env_vars) >= 0

    async def test_set_env_vars(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should set environment variables on a workspace."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Set some test environment variables
        test_vars = [
            {"name": "TEST_VAR_1", "value": "test_value_1"},
            {"name": "TEST_VAR_2", "value": "test_value_2"},
            {"name": "SDK_INTEGRATION_TEST", "value": "true"},
        ]

        await workspace.env_vars.set(test_vars)

        # Verify they were set
        env_vars = await workspace.env_vars.get()
        env_var_names = [ev.name for ev in env_vars]

        assert "TEST_VAR_1" in env_var_names
        assert "TEST_VAR_2" in env_var_names
        assert "SDK_INTEGRATION_TEST" in env_var_names

    async def test_update_env_var_value(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should update an existing environment variable's value."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Set initial value
        await workspace.env_vars.set([{"name": "UPDATE_TEST_VAR", "value": "initial"}])

        # Update the value
        await workspace.env_vars.set([{"name": "UPDATE_TEST_VAR", "value": "updated"}])

        # Verify the update
        env_vars = await workspace.env_vars.get()
        update_var = next((ev for ev in env_vars if ev.name == "UPDATE_TEST_VAR"), None)

        assert update_var is not None
        assert update_var.value == "updated"

    async def test_delete_env_vars_by_name(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should delete environment variables by name."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Ensure we have a variable to delete
        await workspace.env_vars.set([{"name": "TO_DELETE_VAR", "value": "delete_me"}])

        # Verify it exists
        env_vars = await workspace.env_vars.get()
        assert any(ev.name == "TO_DELETE_VAR" for ev in env_vars)

        # Delete by name
        await workspace.env_vars.delete(["TO_DELETE_VAR"])

        # Verify deletion
        env_vars = await workspace.env_vars.get()
        assert not any(ev.name == "TO_DELETE_VAR" for ev in env_vars)

    async def test_delete_multiple_env_vars(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should delete multiple environment variables at once."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Set multiple variables
        await workspace.env_vars.set(
            [
                {"name": "MULTI_DELETE_1", "value": "value1"},
                {"name": "MULTI_DELETE_2", "value": "value2"},
                {"name": "MULTI_DELETE_3", "value": "value3"},
            ]
        )

        # Delete multiple at once
        await workspace.env_vars.delete(
            ["MULTI_DELETE_1", "MULTI_DELETE_2", "MULTI_DELETE_3"]
        )

        # Verify all deleted
        env_vars = await workspace.env_vars.get()
        remaining_names = [ev.name for ev in env_vars]

        assert "MULTI_DELETE_1" not in remaining_names
        assert "MULTI_DELETE_2" not in remaining_names
        assert "MULTI_DELETE_3" not in remaining_names

    async def test_set_env_vars_with_special_characters(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should handle environment variables with special characters in values."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        special_value = "test=value&with?special#chars"
        await workspace.env_vars.set(
            [
                {"name": "SPECIAL_CHARS_VAR", "value": special_value},
            ]
        )

        env_vars = await workspace.env_vars.get()
        special_var = next(
            (ev for ev in env_vars if ev.name == "SPECIAL_CHARS_VAR"), None
        )

        assert special_var is not None
        assert special_var.value == special_value

        # Cleanup
        await workspace.env_vars.delete(["SPECIAL_CHARS_VAR"])
