import pytest

from codesphere import CodesphereSDK
from codesphere.resources.workspace import Workspace


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestEnvVarsIntegration:
    async def test_get_env_vars_empty(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should retrieve environment variables (may be empty initially)."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        env_vars = await workspace.env_vars.get()

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

        test_vars = [
            {"name": "TEST_VAR_1", "value": "test_value_1"},
            {"name": "TEST_VAR_2", "value": "test_value_2"},
            {"name": "SDK_INTEGRATION_TEST", "value": "true"},
        ]

        await workspace.env_vars.set(test_vars)

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

        await workspace.env_vars.set([{"name": "UPDATE_TEST_VAR", "value": "initial"}])

        await workspace.env_vars.set([{"name": "UPDATE_TEST_VAR", "value": "updated"}])

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

        await workspace.env_vars.set([{"name": "TO_DELETE_VAR", "value": "delete_me"}])

        env_vars = await workspace.env_vars.get()
        assert any(ev.name == "TO_DELETE_VAR" for ev in env_vars)

        await workspace.env_vars.delete(["TO_DELETE_VAR"])

        env_vars = await workspace.env_vars.get()
        assert not any(ev.name == "TO_DELETE_VAR" for ev in env_vars)

    async def test_delete_multiple_env_vars(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Should delete multiple environment variables at once."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        await workspace.env_vars.set(
            [
                {"name": "MULTI_DELETE_1", "value": "value1"},
                {"name": "MULTI_DELETE_2", "value": "value2"},
                {"name": "MULTI_DELETE_3", "value": "value3"},
            ]
        )

        await workspace.env_vars.delete(
            ["MULTI_DELETE_1", "MULTI_DELETE_2", "MULTI_DELETE_3"]
        )

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

        await workspace.env_vars.delete(["SPECIAL_CHARS_VAR"])
