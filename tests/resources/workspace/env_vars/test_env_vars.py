"""
Tests for Environment Variables: WorkspaceEnvVarManager and EnvVar model.
"""

import pytest
from dataclasses import dataclass
from typing import Any, Optional

from codesphere.resources.workspace.envVars import EnvVar, WorkspaceEnvVarManager


# -----------------------------------------------------------------------------
# Test Cases
# -----------------------------------------------------------------------------


@dataclass
class EnvVarOperationTestCase:
    """Test case for environment variable operations."""

    name: str
    operation: str
    input_data: Optional[Any] = None
    mock_response: Optional[Any] = None


# -----------------------------------------------------------------------------
# WorkspaceEnvVarManager Tests
# -----------------------------------------------------------------------------


class TestWorkspaceEnvVarManager:
    """Tests for the WorkspaceEnvVarManager class."""

    @pytest.fixture
    def env_var_manager(self, mock_http_client_for_resource, sample_env_var_data):
        """Create a WorkspaceEnvVarManager with mock HTTP client."""
        mock_client = mock_http_client_for_resource(sample_env_var_data)
        manager = WorkspaceEnvVarManager(http_client=mock_client, workspace_id=72678)
        return manager, mock_client

    @pytest.mark.asyncio
    async def test_get_env_vars(self, env_var_manager, sample_env_var_data):
        """Get should return a list of EnvVar models."""
        manager, mock_client = env_var_manager

        result = await manager.get()

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_env_vars_with_list(self, mock_http_client_for_resource):
        """Set should accept a list of EnvVar models."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceEnvVarManager(http_client=mock_client, workspace_id=72678)

        env_vars = [
            EnvVar(name="VAR1", value="value1"),
            EnvVar(name="VAR2", value="value2"),
        ]
        await manager.set(env_vars=env_vars)

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_env_vars_with_dict_list(self, mock_http_client_for_resource):
        """Set should accept a list of dictionaries."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceEnvVarManager(http_client=mock_client, workspace_id=72678)

        env_vars = [
            {"name": "VAR1", "value": "value1"},
            {"name": "VAR2", "value": "value2"},
        ]
        await manager.set(env_vars=env_vars)

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_env_vars_by_name(self, mock_http_client_for_resource):
        """Delete should accept a list of variable names."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceEnvVarManager(http_client=mock_client, workspace_id=72678)

        await manager.delete(items=["VAR1", "VAR2"])

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_env_vars_by_model(self, mock_http_client_for_resource):
        """Delete should accept a list of EnvVar models."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceEnvVarManager(http_client=mock_client, workspace_id=72678)

        env_vars = [
            EnvVar(name="VAR1", value="value1"),
            EnvVar(name="VAR2", value="value2"),
        ]
        await manager.delete(items=env_vars)

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_empty_list_does_nothing(self, mock_http_client_for_resource):
        """Delete with empty list should not make a request."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceEnvVarManager(http_client=mock_client, workspace_id=72678)

        await manager.delete(items=[])

        mock_client.request.assert_not_awaited()


# -----------------------------------------------------------------------------
# EnvVar Model Tests
# -----------------------------------------------------------------------------


class TestEnvVarModel:
    """Tests for the EnvVar model."""

    def test_create_env_var(self):
        """EnvVar should be created with name and value."""
        env_var = EnvVar(name="MY_VAR", value="my_value")

        assert env_var.name == "MY_VAR"
        assert env_var.value == "my_value"

    def test_env_var_from_dict(self):
        """EnvVar should be created from dictionary."""
        env_var = EnvVar.model_validate({"name": "API_KEY", "value": "secret123"})

        assert env_var.name == "API_KEY"
        assert env_var.value == "secret123"

    def test_env_var_dump(self):
        """EnvVar should dump to dictionary correctly."""
        env_var = EnvVar(name="DEBUG", value="true")
        dumped = env_var.model_dump()

        assert dumped == {"name": "DEBUG", "value": "true"}

    def test_env_var_with_empty_value(self):
        """EnvVar should allow empty string value."""
        env_var = EnvVar(name="EMPTY_VAR", value="")

        assert env_var.name == "EMPTY_VAR"
        assert env_var.value == ""

    def test_env_var_with_special_characters(self):
        """EnvVar should handle special characters in values."""
        env_var = EnvVar(
            name="CONNECTION_STRING",
            value="postgresql://user:p@ss=word@localhost:5432/db",
        )

        assert "p@ss=word" in env_var.value
