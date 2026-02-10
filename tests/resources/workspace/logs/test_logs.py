from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from codesphere.exceptions import APIError, ValidationError
from codesphere.resources.workspace.logs import (
    LogEntry,
    LogProblem,
    LogStage,
    WorkspaceLogManager,
)


class TestLogStage:
    def test_enum_values(self):
        assert LogStage.PREPARE.value == "prepare"
        assert LogStage.TEST.value == "test"
        assert LogStage.RUN.value == "run"


class TestLogEntry:
    def test_create_with_data_only(self):
        entry = LogEntry(data="Test log message")
        assert entry.data == "Test log message"
        assert entry.timestamp is None
        assert entry.kind is None

    def test_create_with_all_fields(self):
        entry = LogEntry(
            data="Test message",
            timestamp="2026-02-10T12:00:00Z",
            kind="I",
        )
        assert entry.data == "Test message"
        assert entry.timestamp == "2026-02-10T12:00:00Z"
        assert entry.kind == "I"

    def test_from_dict(self):
        data = {"data": "Hello", "timestamp": "2026-02-10T12:00:00Z"}
        entry = LogEntry.model_validate(data)
        assert entry.data == "Hello"

    def test_get_text(self):
        entry = LogEntry(data="Log content")
        assert entry.get_text() == "Log content"

    def test_get_text_empty(self):
        entry = LogEntry()
        assert entry.get_text() == ""


class TestLogProblem:
    def test_create_problem(self):
        problem = LogProblem(status=400, reason="Workspace is not running")
        assert problem.status == 400
        assert problem.reason == "Workspace is not running"
        assert problem.detail is None

    def test_create_problem_with_detail(self):
        problem = LogProblem(
            status=404,
            reason="Not found",
            detail="Workspace 123 does not exist",
        )
        assert problem.status == 404
        assert problem.detail == "Workspace 123 does not exist"


async def mock_stream_logs_factory(entries: list[LogEntry], capture_endpoint: list):
    """Factory to create a mock _stream_logs that captures the endpoint."""

    async def mock_stream_logs(endpoint: str):
        capture_endpoint.append(endpoint)
        for entry in entries:
            yield entry

    return mock_stream_logs


class TestWorkspaceLogManager:
    @pytest.fixture
    def mock_http_client(self):
        client = MagicMock()
        client._get_client = MagicMock()
        return client

    @pytest.fixture
    def log_manager(self, mock_http_client):
        return WorkspaceLogManager(mock_http_client, workspace_id=123)

    def test_init(self, log_manager, mock_http_client):
        assert log_manager._http_client == mock_http_client
        assert log_manager._workspace_id == 123

    @pytest.mark.asyncio
    async def test_stream_builds_correct_endpoint(self, log_manager):
        """Test that stream() builds the correct endpoint URL."""
        captured_endpoints: list[str] = []

        async def mock_stream_logs(endpoint: str, timeout: float = None):
            captured_endpoints.append(endpoint)
            return
            yield  # Make it a generator

        log_manager._stream_logs = mock_stream_logs

        async for _ in log_manager.stream(stage=LogStage.PREPARE, step=1):
            pass

        assert captured_endpoints == ["/workspaces/123/logs/prepare/1"]

    @pytest.mark.asyncio
    async def test_stream_with_string_stage(self, log_manager):
        """Test that stream() accepts string stage values."""
        captured_endpoints: list[str] = []

        async def mock_stream_logs(endpoint: str, timeout: float = None):
            captured_endpoints.append(endpoint)
            return
            yield

        log_manager._stream_logs = mock_stream_logs

        async for _ in log_manager.stream(stage="test", step=2):
            pass

        assert captured_endpoints == ["/workspaces/123/logs/test/2"]

    @pytest.mark.asyncio
    async def test_stream_server_builds_correct_endpoint(self, log_manager):
        """Test that stream_server() builds the correct endpoint URL."""
        captured_endpoints: list[str] = []

        async def mock_stream_logs(endpoint: str, timeout: float = None):
            captured_endpoints.append(endpoint)
            return
            yield

        log_manager._stream_logs = mock_stream_logs

        async for _ in log_manager.stream_server(step=1, server="web"):
            pass

        assert captured_endpoints == ["/workspaces/123/logs/run/1/server/web"]

    @pytest.mark.asyncio
    async def test_stream_replica_builds_correct_endpoint(self, log_manager):
        """Test that stream_replica() builds the correct endpoint URL."""
        captured_endpoints: list[str] = []

        async def mock_stream_logs(endpoint: str, timeout: float = None):
            captured_endpoints.append(endpoint)
            return
            yield

        log_manager._stream_logs = mock_stream_logs

        async for _ in log_manager.stream_replica(step=2, replica="replica-1"):
            pass

        assert captured_endpoints == ["/workspaces/123/logs/run/2/replica/replica-1"]

    @pytest.mark.asyncio
    async def test_collect_returns_list(self, log_manager):
        """Test that collect() returns a list of log entries."""
        entries = [
            LogEntry(data="Log 1"),
            LogEntry(data="Log 2"),
            LogEntry(data="Log 3"),
        ]

        async def mock_stream_logs(endpoint: str, timeout: float = None):
            for entry in entries:
                yield entry

        log_manager._stream_logs = mock_stream_logs

        result = await log_manager.collect(stage=LogStage.PREPARE, step=1)

        assert len(result) == 3
        assert result[0].data == "Log 1"
        assert result[2].data == "Log 3"

    @pytest.mark.asyncio
    async def test_collect_with_max_entries(self, log_manager):
        """Test that collect() respects max_entries limit."""
        entries = [
            LogEntry(data="Log 1"),
            LogEntry(data="Log 2"),
            LogEntry(data="Log 3"),
        ]

        async def mock_stream_logs(endpoint: str, timeout: float = None):
            for entry in entries:
                yield entry

        log_manager._stream_logs = mock_stream_logs

        result = await log_manager.collect(
            stage=LogStage.PREPARE, step=1, max_entries=2
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_collect_server_returns_list(self, log_manager):
        """Test that collect_server() returns a list of log entries."""
        entries = [LogEntry(data="Server log 1")]

        async def mock_stream_logs(endpoint: str, timeout: float = None):
            for entry in entries:
                yield entry

        log_manager._stream_logs = mock_stream_logs

        result = await log_manager.collect_server(step=1, server="web")

        assert len(result) == 1
        assert result[0].data == "Server log 1"

    @pytest.mark.asyncio
    async def test_collect_replica_returns_list(self, log_manager):
        """Test that collect_replica() returns a list of log entries."""
        entries = [LogEntry(data="Replica log 1")]

        async def mock_stream_logs(endpoint: str, timeout: float = None):
            for entry in entries:
                yield entry

        log_manager._stream_logs = mock_stream_logs

        result = await log_manager.collect_replica(step=1, replica="replica-1")

        assert len(result) == 1
        assert result[0].data == "Replica log 1"

    @pytest.mark.asyncio
    async def test_process_sse_event_raises_on_problem(self, log_manager):
        """Test that problem events raise appropriate exceptions."""
        problem_data = '{"status": 400, "reason": "Workspace is not running"}'

        with pytest.raises(ValidationError) as exc_info:
            await log_manager._process_sse_event("problem", problem_data)

        assert "Workspace is not running" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_sse_event_raises_api_error_for_non_400(self, log_manager):
        """Test that non-400 problem events raise APIError."""
        problem_data = '{"status": 404, "reason": "Workspace not found"}'

        with pytest.raises(APIError) as exc_info:
            await log_manager._process_sse_event("problem", problem_data)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_process_sse_event_data_does_not_raise(self, log_manager):
        """Test that data events do not raise exceptions."""
        data = '{"data": "Test log"}'
        # Should not raise
        await log_manager._process_sse_event("data", data)

    @pytest.mark.asyncio
    async def test_process_sse_event_invalid_json_raises(self, log_manager):
        """Test that invalid JSON in problem events raises APIError."""
        with pytest.raises(APIError) as exc_info:
            await log_manager._process_sse_event("problem", "invalid json")

        assert "Invalid problem event" in str(exc_info.value)
