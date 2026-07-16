"""SSE log streaming through the generated sync LogStream."""

import httpx
import pytest

from codesphere.models.logs import LogStage, StageTarget

SSE_BODY = (
    "event: data\n"
    'data: {"timestamp": "t1", "kind": "I", "data": "line one"}\n'
    "\n"
    "event: data\n"
    'data: [{"timestamp": "t2", "kind": "E", "data": "line two"}]\n'
    "\n"
    "event: end\n"
    "data: done\n"
    "\n"
)


@pytest.fixture
def workspace(sdk, mock_api, sample_workspace_json):
    mock_api.get("/workspaces/5").respond(200, json=sample_workspace_json)
    return sdk.workspaces.get(5)


class TestSyncLogStream:
    def test_stream_yields_entries_until_end_event(self, workspace, mock_api):
        mock_api.get("/workspaces/5/logs/prepare/0").respond(200, text=SSE_BODY)

        entries = list(workspace.logs.stream(StageTarget(LogStage.PREPARE, step=0)))

        assert [e.data for e in entries] == ["line one", "line two"]
        assert entries[1].kind == "E"

    def test_collect_with_max_entries(self, workspace, mock_api):
        mock_api.get("/workspaces/5/logs/run/1").respond(200, text=SSE_BODY)

        entries = workspace.logs.collect(
            StageTarget(LogStage.RUN, step=1), max_entries=1
        )

        assert len(entries) == 1

    def test_open_as_context_manager(self, workspace, mock_api):
        mock_api.get("/workspaces/5/logs/test/0").respond(200, text=SSE_BODY)

        with workspace.logs.open(StageTarget(LogStage.TEST, step=0)) as stream:
            first = next(iter(stream))

        assert first.data == "line one"

    def test_http_error_maps_to_sdk_error(self, workspace, mock_api):
        from codesphere import NotFoundError

        mock_api.get("/workspaces/5/logs/run/9").respond(404, json={"message": "no"})

        with (
            pytest.raises(NotFoundError),
            workspace.logs.open(StageTarget(LogStage.RUN, step=9)),
        ):
            pass

    def test_read_timeout_maps_to_timeout_error(self, workspace, mock_api):
        mock_api.get("/workspaces/5/logs/run/2").mock(
            side_effect=httpx.ReadTimeout("slow")
        )

        with (
            pytest.raises(httpx.ReadTimeout),
            workspace.logs.open(StageTarget(LogStage.RUN, step=2), timeout=0.1),
        ):
            pass
