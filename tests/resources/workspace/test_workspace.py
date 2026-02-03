"""
Tests for Workspace resources: WorkspacesResource and Workspace model.
"""

import pytest

from codesphere.resources.workspace import (
    Workspace,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceStatus,
)


# -----------------------------------------------------------------------------
# WorkspacesResource Tests
# -----------------------------------------------------------------------------


class TestWorkspacesResource:
    """Tests for the WorkspacesResource class."""

    @pytest.mark.asyncio
    async def test_list_by_team(
        self, workspaces_resource_factory, sample_workspace_list_data
    ):
        """List workspaces should return a list of Workspace models."""
        resource, mock_client = workspaces_resource_factory(sample_workspace_list_data)

        result = await resource.list(team_id=12345)

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(ws, Workspace) for ws in result)

    @pytest.mark.asyncio
    async def test_list_by_team_empty(self, workspaces_resource_factory):
        """List workspaces should handle empty response."""
        resource, _ = workspaces_resource_factory([])

        result = await resource.list(team_id=12345)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_workspace_by_id(
        self, workspaces_resource_factory, sample_workspace_data
    ):
        """Get workspace should return a single Workspace model."""
        resource, mock_client = workspaces_resource_factory(sample_workspace_data)

        result = await resource.get(workspace_id=72678)

        assert isinstance(result, Workspace)
        assert result.id == sample_workspace_data["id"]
        assert result.name == sample_workspace_data["name"]

    @pytest.mark.asyncio
    async def test_create_workspace(
        self, workspaces_resource_factory, sample_workspace_data
    ):
        """Create workspace should return the created Workspace model."""
        resource, mock_client = workspaces_resource_factory(sample_workspace_data)
        payload = WorkspaceCreate(
            team_id=12345,
            name="new-workspace",
            plan_id=8,
        )

        result = await resource.create(payload=payload)

        assert isinstance(result, Workspace)
        mock_client.request.assert_awaited_once()


# -----------------------------------------------------------------------------
# Workspace Model Tests
# -----------------------------------------------------------------------------


class TestWorkspaceModel:
    """Tests for the Workspace model and its methods."""

    @pytest.mark.asyncio
    async def test_update_workspace(self, workspace_model_factory):
        """Workspace.update() should update the workspace and local model."""
        workspace, mock_client = workspace_model_factory()

        update_data = WorkspaceUpdate(name="updated-name", plan_id=10)
        await workspace.update(data=update_data)

        mock_client.request.assert_awaited_once()
        assert workspace.name == "updated-name"
        assert workspace.plan_id == 10

    @pytest.mark.asyncio
    async def test_delete_workspace(self, workspace_model_factory):
        """Workspace.delete() should call the delete operation."""
        workspace, mock_client = workspace_model_factory()

        await workspace.delete()

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_status(self, workspace_model_factory):
        """Workspace.get_status() should return WorkspaceStatus."""
        status_response = {"isRunning": True}
        workspace, mock_client = workspace_model_factory(response_data=status_response)

        result = await workspace.get_status()

        assert isinstance(result, WorkspaceStatus)
        assert result.is_running is True

    @pytest.mark.asyncio
    async def test_execute_command(self, workspace_model_factory):
        """Workspace.execute_command() should execute a command and return output."""
        command_response = {
            "command": "echo Hello",
            "workingDir": "/home/user",
            "output": "Hello\n",
            "error": "",
        }
        workspace, mock_client = workspace_model_factory(response_data=command_response)

        result = await workspace.execute_command(
            command="echo Hello", env={"USER": "test"}
        )

        assert result.command == "echo Hello"
        assert result.output == "Hello\n"

    def test_env_vars_raises_without_http_client(self, sample_workspace_data):
        """Accessing env_vars without valid HTTP client should raise RuntimeError."""
        workspace = Workspace.model_validate(sample_workspace_data)

        with pytest.raises(RuntimeError, match="detached model"):
            _ = workspace.env_vars


# -----------------------------------------------------------------------------
# WorkspaceCreate Schema Tests
# -----------------------------------------------------------------------------


class TestWorkspaceCreateSchema:
    """Tests for the WorkspaceCreate schema."""

    def test_create_with_required_fields(self):
        """WorkspaceCreate should be created with required fields."""
        create = WorkspaceCreate(
            team_id=12345,
            name="test-workspace",
            plan_id=8,
        )

        assert create.team_id == 12345
        assert create.name == "test-workspace"
        assert create.plan_id == 8

    def test_create_with_optional_fields(self):
        """WorkspaceCreate should accept optional fields."""
        create = WorkspaceCreate(
            team_id=12345,
            name="test-workspace",
            plan_id=8,
            base_image="ubuntu:22.04",
            git_url="https://github.com/example/repo.git",
            initial_branch="main",
            replicas=2,
        )

        assert create.base_image == "ubuntu:22.04"
        assert create.git_url == "https://github.com/example/repo.git"
        assert create.initial_branch == "main"
        assert create.replicas == 2

    def test_dump_to_camel_case(self):
        """WorkspaceCreate should dump to camelCase for API requests."""
        create = WorkspaceCreate(
            team_id=12345,
            name="test",
            plan_id=8,
            is_private_repo=True,
        )
        dumped = create.model_dump(by_alias=True)

        assert "teamId" in dumped
        assert "planId" in dumped
        assert "isPrivateRepo" in dumped


# -----------------------------------------------------------------------------
# WorkspaceUpdate Schema Tests
# -----------------------------------------------------------------------------


class TestWorkspaceUpdateSchema:
    """Tests for the WorkspaceUpdate schema."""

    def test_all_fields_optional(self):
        """WorkspaceUpdate should have all fields optional."""
        update = WorkspaceUpdate()

        assert update.name is None
        assert update.plan_id is None
        assert update.replicas is None

    def test_partial_update(self):
        """WorkspaceUpdate should allow partial updates."""
        update = WorkspaceUpdate(name="new-name")

        assert update.name == "new-name"
        assert update.plan_id is None

    def test_dump_excludes_none_values(self):
        """WorkspaceUpdate dump should exclude None values."""
        update = WorkspaceUpdate(name="updated", plan_id=10)
        dumped = update.model_dump(exclude_none=True, by_alias=True)

        assert "name" in dumped
        assert "planId" in dumped
        assert "replicas" not in dumped


# -----------------------------------------------------------------------------
# WorkspaceStatus Schema Tests
# -----------------------------------------------------------------------------


class TestWorkspaceStatusSchema:
    """Tests for the WorkspaceStatus schema."""

    def test_create_from_camel_case(self):
        """WorkspaceStatus should be created from camelCase JSON."""
        status = WorkspaceStatus.model_validate({"isRunning": True})
        assert status.is_running is True

    def test_running_status(self):
        """WorkspaceStatus should correctly represent running state."""
        status = WorkspaceStatus(is_running=True)
        assert status.is_running is True

    def test_stopped_status(self):
        """WorkspaceStatus should correctly represent stopped state."""
        status = WorkspaceStatus(is_running=False)
        assert status.is_running is False
