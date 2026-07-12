from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from codesphere.exceptions import APIError, ValidationError
from codesphere.resources.workspace.logs import (
    LogEntry,
    LogProblem,
    LogStage,
    LogStream,
    ReplicaTarget,
    ServerTarget,
    StageTarget,
    WorkspaceLogManager,
)
from codesphere.resources.workspace.logs.operations import (
    _STREAM_REPLICA_LOGS_OP,
    _STREAM_SERVER_LOGS_OP,
    _STREAM_STAGE_LOGS_OP,
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


class TestStreamOperations:
    def test_stream_stage_logs_op(self):
        assert (
            _STREAM_STAGE_LOGS_OP.endpoint_template
            == "/workspaces/{id}/logs/{stage}/{step}"
        )
        assert _STREAM_STAGE_LOGS_OP.entry_model == LogEntry

    def test_stream_server_logs_op(self):
        assert (
            _STREAM_SERVER_LOGS_OP.endpoint_template
            == "/workspaces/{id}/logs/run/{step}/server/{server}"
        )
        assert _STREAM_SERVER_LOGS_OP.entry_model == LogEntry

    def test_stream_replica_logs_op(self):
        assert (
            _STREAM_REPLICA_LOGS_OP.endpoint_template
            == "/workspaces/{id}/logs/run/{step}/replica/{replica}"
        )
        assert _STREAM_REPLICA_LOGS_OP.entry_model == LogEntry


class TestLogStream:
    def test_init(self):
        mock_client = MagicMock()
        stream = LogStream(mock_client, "/test/endpoint", LogEntry, timeout=30.0)
        assert stream._http_client == mock_client
        assert stream._endpoint == "/test/endpoint"
        assert stream._entry_model == LogEntry
        assert stream._timeout == 30.0

    def test_init_no_timeout(self):
        mock_client = MagicMock()
        stream = LogStream(mock_client, "/test/endpoint", LogEntry)
        assert stream._timeout is None

    def test_handle_problem_validation_error(self):
        mock_client = MagicMock()
        stream = LogStream(mock_client, "/test", LogEntry)

        with pytest.raises(ValidationError):
            stream._handle_problem('{"status": 400, "reason": "Bad request"}')

    def test_handle_problem_api_error(self):
        mock_client = MagicMock()
        stream = LogStream(mock_client, "/test", LogEntry)

        with pytest.raises(APIError) as exc_info:
            stream._handle_problem('{"status": 404, "reason": "Not found"}')
        assert exc_info.value.status_code == 404

    def test_handle_problem_invalid_json(self):
        mock_client = MagicMock()
        stream = LogStream(mock_client, "/test", LogEntry)

        with pytest.raises(APIError) as exc_info:
            stream._handle_problem("invalid json")
        assert "Invalid problem event" in str(exc_info.value)

    def test_parse_data_single_entry(self):
        mock_client = MagicMock()
        stream = LogStream(mock_client, "/test", LogEntry)

        entries = stream._parse_data('{"data": "test log", "kind": "I"}')
        assert len(entries) == 1
        assert entries[0].data == "test log"
        assert entries[0].kind == "I"

    def test_parse_data_array(self):
        mock_client = MagicMock()
        stream = LogStream(mock_client, "/test", LogEntry)

        entries = stream._parse_data('[{"data": "log1"}, {"data": "log2"}]')
        assert len(entries) == 2
        assert entries[0].data == "log1"
        assert entries[1].data == "log2"

    def test_parse_data_invalid_json(self):
        mock_client = MagicMock()
        stream = LogStream(mock_client, "/test", LogEntry)

        entries = stream._parse_data("invalid")
        assert len(entries) == 0


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
        assert log_manager.workspace_id == 123

    def test_build_endpoint(self, log_manager):
        endpoint = log_manager._build_endpoint(
            _STREAM_STAGE_LOGS_OP, stage="prepare", step=0
        )
        assert endpoint == "/workspaces/123/logs/prepare/0"

    def test_build_endpoint_server(self, log_manager):
        endpoint = log_manager._build_endpoint(
            _STREAM_SERVER_LOGS_OP, step=0, server="web"
        )
        assert endpoint == "/workspaces/123/logs/run/0/server/web"

    def test_open_stage_target(self, log_manager):
        stream = log_manager.open(StageTarget(stage=LogStage.PREPARE, step=0))
        assert isinstance(stream, LogStream)
        assert stream._endpoint == "/workspaces/123/logs/prepare/0"
        assert stream._entry_model == LogEntry

    def test_open_stage_target_with_string_stage(self, log_manager):
        stream = log_manager.open(StageTarget(stage="test", step=1))
        assert stream._endpoint == "/workspaces/123/logs/test/1"

    def test_open_with_timeout(self, log_manager):
        stream = log_manager.open(StageTarget(stage="run", step=0), timeout=60.0)
        assert stream._timeout == 60.0

    def test_open_server_target(self, log_manager):
        stream = log_manager.open(ServerTarget(step=0, server="web"))
        assert isinstance(stream, LogStream)
        assert stream._endpoint == "/workspaces/123/logs/run/0/server/web"

    def test_open_replica_target(self, log_manager):
        stream = log_manager.open(ReplicaTarget(step=0, replica="replica-1"))
        assert isinstance(stream, LogStream)
        assert stream._endpoint == "/workspaces/123/logs/run/0/replica/replica-1"


class FakeStream:
    """Minimal LogStream stand-in: async CM yielding canned entries."""

    def __init__(self, entries):
        self._entries = entries

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for entry in self._entries:
            yield entry


class TestUnifiedStreamCollect:
    @pytest.fixture
    def log_manager(self):
        return WorkspaceLogManager(MagicMock(), workspace_id=123)

    @pytest.mark.asyncio
    async def test_collect_with_target(self, log_manager, monkeypatch):
        entries = [LogEntry(data="a"), LogEntry(data="b"), LogEntry(data="c")]
        opened = []

        def fake_open(target, timeout=None):
            opened.append((target, timeout))
            return FakeStream(entries)

        monkeypatch.setattr(log_manager, "open", fake_open)
        result = await log_manager.collect(ServerTarget(step=1, server="web"))

        assert result == entries
        assert opened == [(ServerTarget(step=1, server="web"), 30.0)]

    @pytest.mark.asyncio
    async def test_collect_respects_max_entries(self, log_manager, monkeypatch):
        entries = [LogEntry(data=str(i)) for i in range(10)]
        monkeypatch.setattr(
            log_manager, "open", lambda t, timeout=None: FakeStream(entries)
        )

        result = await log_manager.collect(
            StageTarget(stage="run", step=0), max_entries=3
        )
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_stream_with_target(self, log_manager, monkeypatch):
        entries = [LogEntry(data="x")]
        monkeypatch.setattr(
            log_manager, "open", lambda t, timeout=None: FakeStream(entries)
        )

        got = [e async for e in log_manager.stream(StageTarget(stage="run", step=1))]
        assert got == entries


class TestDeprecatedLogAliases:
    @pytest.fixture
    def log_manager(self):
        return WorkspaceLogManager(MagicMock(), workspace_id=123)

    def test_open_stream_warns_and_delegates(self, log_manager):
        with pytest.warns(DeprecationWarning, match="open_stream"):
            stream = log_manager.open_stream(stage=LogStage.PREPARE, step=0)
        assert stream._endpoint == "/workspaces/123/logs/prepare/0"

    def test_open_server_stream_warns(self, log_manager):
        with pytest.warns(DeprecationWarning, match="open_server_stream"):
            stream = log_manager.open_server_stream(step=0, server="web")
        assert stream._endpoint == "/workspaces/123/logs/run/0/server/web"

    def test_open_replica_stream_warns(self, log_manager):
        with pytest.warns(DeprecationWarning, match="open_replica_stream"):
            stream = log_manager.open_replica_stream(step=0, replica="r-1")
        assert stream._endpoint == "/workspaces/123/logs/run/0/replica/r-1"

    @pytest.mark.asyncio
    async def test_legacy_collect_stage_form_warns(self, log_manager, monkeypatch):
        entries = [LogEntry(data="legacy")]
        opened = []

        def fake_open(target, timeout=None):
            opened.append(target)
            return FakeStream(entries)

        monkeypatch.setattr(log_manager, "open", fake_open)
        with pytest.warns(DeprecationWarning, match="collect"):
            result = await log_manager.collect("run", 1)

        assert result == entries
        assert opened == [StageTarget(stage="run", step=1)]

    @pytest.mark.asyncio
    async def test_collect_server_warns_and_delegates(self, log_manager, monkeypatch):
        entries = [LogEntry(data="srv")]
        monkeypatch.setattr(
            log_manager, "open", lambda t, timeout=None: FakeStream(entries)
        )

        with pytest.warns(DeprecationWarning, match="collect_server"):
            result = await log_manager.collect_server(step=1, server="web")
        assert result == entries

    @pytest.mark.asyncio
    async def test_collect_replica_warns_and_delegates(self, log_manager, monkeypatch):
        entries = [LogEntry(data="rep")]
        monkeypatch.setattr(
            log_manager, "open", lambda t, timeout=None: FakeStream(entries)
        )

        with pytest.warns(DeprecationWarning, match="collect_replica"):
            result = await log_manager.collect_replica(step=1, replica="r-1")
        assert result == entries

    @pytest.mark.asyncio
    async def test_stream_server_warns_and_delegates(self, log_manager, monkeypatch):
        entries = [LogEntry(data="srv")]
        monkeypatch.setattr(
            log_manager, "open", lambda t, timeout=None: FakeStream(entries)
        )

        with pytest.warns(DeprecationWarning, match="stream_server"):
            got = [e async for e in log_manager.stream_server(step=1, server="web")]
        assert got == entries

    @pytest.mark.asyncio
    async def test_stream_replica_warns_and_delegates(self, log_manager, monkeypatch):
        entries = [LogEntry(data="rep")]
        monkeypatch.setattr(
            log_manager, "open", lambda t, timeout=None: FakeStream(entries)
        )

        with pytest.warns(DeprecationWarning, match="stream_replica"):
            got = [e async for e in log_manager.stream_replica(step=1, replica="r-1")]
        assert got == entries


class TestLogKind:
    def test_known_kinds_are_enum(self):
        from codesphere.resources.workspace.logs import LogKind

        entry = LogEntry.model_validate({"kind": "I", "data": "hi"})
        assert entry.kind is LogKind.INFO

    def test_unknown_kind_falls_back_to_str(self):
        entry = LogEntry.model_validate({"kind": "X", "data": "hi"})
        assert entry.kind == "X"
