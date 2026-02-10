from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from codesphere.resources.workspace.landscape import (
    PipelineStage,
    PipelineState,
    PipelineStatus,
    PipelineStatusList,
    StepStatus,
)
from codesphere.resources.workspace.landscape.models import WorkspaceLandscapeManager


class TestPipelineSchemas:
    def test_pipeline_stage_enum_values(self):
        assert PipelineStage.PREPARE.value == "prepare"
        assert PipelineStage.TEST.value == "test"
        assert PipelineStage.RUN.value == "run"

    def test_pipeline_state_enum_values(self):
        assert PipelineState.WAITING.value == "waiting"
        assert PipelineState.RUNNING.value == "running"
        assert PipelineState.SUCCESS.value == "success"
        assert PipelineState.FAILURE.value == "failure"
        assert PipelineState.ABORTED.value == "aborted"

    def test_step_status_create(self):
        status = StepStatus(state=PipelineState.RUNNING)
        assert status.state == PipelineState.RUNNING
        assert status.started_at is None
        assert status.finished_at is None

    def test_step_status_with_timestamps(self):
        status = StepStatus(
            state=PipelineState.SUCCESS,
            started_at="2026-02-10T10:00:00Z",
            finished_at="2026-02-10T10:05:00Z",
        )
        assert status.state == PipelineState.SUCCESS
        assert status.started_at == "2026-02-10T10:00:00Z"
        assert status.finished_at == "2026-02-10T10:05:00Z"

    def test_pipeline_status_create(self):
        status = PipelineStatus(
            state=PipelineState.RUNNING,
            steps=[StepStatus(state=PipelineState.SUCCESS)],
            replica="replica-1",
            server="web",
        )
        assert status.state == PipelineState.RUNNING
        assert len(status.steps) == 1
        assert status.replica == "replica-1"
        assert status.server == "web"

    def test_pipeline_status_list(self):
        statuses = [
            PipelineStatus(
                state=PipelineState.SUCCESS,
                steps=[],
                replica="replica-1",
                server="web",
            ),
            PipelineStatus(
                state=PipelineState.RUNNING,
                steps=[],
                replica="replica-2",
                server="web",
            ),
        ]
        status_list = PipelineStatusList(root=statuses)

        assert len(status_list) == 2
        assert status_list[0].replica == "replica-1"
        assert status_list[1].state == PipelineState.RUNNING


class TestWorkspaceLandscapeManagerPipeline:
    @pytest.fixture
    def mock_http_client(self):
        client = MagicMock()
        client._get_client = MagicMock()
        return client

    @pytest.fixture
    def landscape_manager(self, mock_http_client):
        return WorkspaceLandscapeManager(mock_http_client, workspace_id=123)

    @pytest.mark.asyncio
    async def test_start_stage_with_enum(self, landscape_manager):
        """Test start_stage with PipelineStage enum."""
        landscape_manager._execute_operation = AsyncMock()

        await landscape_manager.start_stage(PipelineStage.PREPARE)

        landscape_manager._execute_operation.assert_called_once()
        call_args = landscape_manager._execute_operation.call_args
        assert call_args.kwargs["stage"] == "prepare"

    @pytest.mark.asyncio
    async def test_start_stage_with_string(self, landscape_manager):
        """Test start_stage with string stage."""
        landscape_manager._execute_operation = AsyncMock()

        await landscape_manager.start_stage("run")

        landscape_manager._execute_operation.assert_called_once()
        call_args = landscape_manager._execute_operation.call_args
        assert call_args.kwargs["stage"] == "run"

    @pytest.mark.asyncio
    async def test_start_stage_with_profile(self, landscape_manager):
        """Test start_stage with a profile name."""
        landscape_manager._execute_operation = AsyncMock()

        await landscape_manager.start_stage(PipelineStage.RUN, profile="production")

        landscape_manager._execute_operation.assert_called_once()
        call_args = landscape_manager._execute_operation.call_args
        assert call_args.kwargs["stage"] == "run"
        assert call_args.kwargs["profile"] == "production"

    @pytest.mark.asyncio
    async def test_start_stage_invalid_profile_name(self, landscape_manager):
        """Test start_stage with invalid profile name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid profile name"):
            await landscape_manager.start_stage(
                PipelineStage.RUN, profile="invalid profile!"
            )

    @pytest.mark.asyncio
    async def test_stop_stage(self, landscape_manager):
        """Test stop_stage."""
        landscape_manager._execute_operation = AsyncMock()

        await landscape_manager.stop_stage(PipelineStage.RUN)

        landscape_manager._execute_operation.assert_called_once()
        call_args = landscape_manager._execute_operation.call_args
        assert call_args.kwargs["stage"] == "run"

    @pytest.mark.asyncio
    async def test_get_stage_status(self, landscape_manager):
        """Test get_stage_status returns PipelineStatusList."""
        mock_status = PipelineStatusList(
            root=[
                PipelineStatus(
                    state=PipelineState.RUNNING,
                    steps=[],
                    replica="replica-1",
                    server="web",
                )
            ]
        )
        landscape_manager._execute_operation = AsyncMock(return_value=mock_status)

        result = await landscape_manager.get_stage_status(PipelineStage.RUN)

        assert len(result) == 1
        assert result[0].state == PipelineState.RUNNING

    @pytest.mark.asyncio
    async def test_wait_for_stage_completes_immediately(self, landscape_manager):
        """Test wait_for_stage when stage is already complete."""
        mock_status = PipelineStatusList(
            root=[
                PipelineStatus(
                    state=PipelineState.SUCCESS,
                    steps=[],
                    replica="replica-1",
                    server="web",
                )
            ]
        )
        landscape_manager._execute_operation = AsyncMock(return_value=mock_status)

        result = await landscape_manager.wait_for_stage(PipelineStage.PREPARE)

        assert len(result) == 1
        assert result[0].state == PipelineState.SUCCESS

    @pytest.mark.asyncio
    async def test_wait_for_stage_polls_until_complete(self, landscape_manager):
        """Test wait_for_stage polls until stage completes."""
        running_status = PipelineStatusList(
            root=[
                PipelineStatus(
                    state=PipelineState.RUNNING,
                    steps=[],
                    replica="replica-1",
                    server="web",
                )
            ]
        )
        success_status = PipelineStatusList(
            root=[
                PipelineStatus(
                    state=PipelineState.SUCCESS,
                    steps=[],
                    replica="replica-1",
                    server="web",
                )
            ]
        )

        landscape_manager._execute_operation = AsyncMock(
            side_effect=[running_status, running_status, success_status]
        )

        result = await landscape_manager.wait_for_stage(
            PipelineStage.PREPARE, poll_interval=0.01
        )

        assert result[0].state == PipelineState.SUCCESS
        assert landscape_manager._execute_operation.call_count == 3

    @pytest.mark.asyncio
    async def test_wait_for_stage_timeout(self, landscape_manager):
        """Test wait_for_stage raises TimeoutError."""
        running_status = PipelineStatusList(
            root=[
                PipelineStatus(
                    state=PipelineState.RUNNING,
                    steps=[],
                    replica="replica-1",
                    server="web",
                )
            ]
        )
        landscape_manager._execute_operation = AsyncMock(return_value=running_status)

        with pytest.raises(TimeoutError, match="did not complete"):
            await landscape_manager.wait_for_stage(
                PipelineStage.PREPARE, timeout=0.05, poll_interval=0.01
            )

    @pytest.mark.asyncio
    async def test_wait_for_stage_invalid_poll_interval(self, landscape_manager):
        """Test wait_for_stage with invalid poll_interval raises ValueError."""
        with pytest.raises(ValueError, match="poll_interval must be greater than 0"):
            await landscape_manager.wait_for_stage(
                PipelineStage.PREPARE, poll_interval=0
            )
