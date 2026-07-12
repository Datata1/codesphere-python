from __future__ import annotations

import asyncio
import json
import logging
import warnings
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from ....core.base import WorkspaceScopedResource
from ....core.operations import StreamOperation
from ....exceptions import APIError, ValidationError, raise_for_status
from ....http_client import APIHttpClient
from .operations import (
    _STREAM_REPLICA_LOGS_OP,
    _STREAM_SERVER_LOGS_OP,
    _STREAM_STAGE_LOGS_OP,
)
from .schemas import LogEntry, LogProblem, LogStage

log = logging.getLogger(__name__)

# SSE event names that terminate a stream.
_STREAM_END_EVENTS = frozenset({"end", "close", "done", "complete"})


@dataclass(frozen=True, slots=True)
class StageTarget:
    """Logs of a pipeline stage (prepare/test/run)."""

    stage: LogStage | str
    step: int = 0


@dataclass(frozen=True, slots=True)
class ServerTarget:
    """Run logs of a specific server in a Multi Server Deployment."""

    step: int
    server: str


@dataclass(frozen=True, slots=True)
class ReplicaTarget:
    """Run logs of a specific replica."""

    step: int
    replica: str


type LogTarget = StageTarget | ServerTarget | ReplicaTarget


def _resolve_target(
    target: LogTarget,
) -> tuple[StreamOperation[LogEntry], dict[str, Any]]:
    match target:
        case StageTarget(stage=stage, step=step):
            stage_value = stage.value if isinstance(stage, LogStage) else stage
            return _STREAM_STAGE_LOGS_OP, {"stage": stage_value, "step": step}
        case ServerTarget(step=step, server=server):
            return _STREAM_SERVER_LOGS_OP, {"step": step, "server": server}
        case ReplicaTarget(step=step, replica=replica):
            return _STREAM_REPLICA_LOGS_OP, {"step": step, "replica": replica}
    raise TypeError(f"Unsupported log target: {target!r}")


def _deprecated(old: str, new: str) -> None:
    warnings.warn(
        f"'{old}' is deprecated; use '{new}' instead.",
        DeprecationWarning,
        stacklevel=3,
    )


class LogStream:
    """Async context manager for streaming logs via SSE."""

    def __init__(
        self,
        http_client: APIHttpClient,
        endpoint: str,
        entry_model: type[LogEntry],
        timeout: float | None = None,
    ):
        self._http_client = http_client
        self._endpoint = endpoint
        self._entry_model = entry_model
        self._timeout = timeout
        self._response: httpx.Response | None = None
        self._stream_context: Any = None

    async def __aenter__(self) -> LogStream:
        headers = {"Accept": "text/event-stream"}
        self._stream_context = self._http_client.stream(
            "GET",
            self._endpoint,
            headers=headers,
            timeout=self._http_client.stream_timeout,
        )
        self._response = await self._stream_context.__aenter__()

        if not self._response.is_success:
            await self._response.aread()
            raise_for_status(self._response)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._stream_context:
            await self._stream_context.__aexit__(exc_type, exc_val, exc_tb)

    def __aiter__(self) -> AsyncIterator[LogEntry]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[LogEntry]:
        if self._response is None:
            raise RuntimeError("LogStream must be used as async context manager")

        if self._timeout is not None:
            async with asyncio.timeout(self._timeout):
                async for entry in self._parse_sse_stream():
                    yield entry
        else:
            async for entry in self._parse_sse_stream():
                yield entry

    async def _parse_sse_stream(self) -> AsyncIterator[LogEntry]:
        if self._response is None:
            raise RuntimeError("LogStream must be used as async context manager")

        event_type: str | None = None
        data_buffer: list[str] = []

        async for line in self._response.aiter_lines():
            line = line.strip()

            if not line:
                if event_type and data_buffer:
                    data_str = "\n".join(data_buffer)

                    if event_type in _STREAM_END_EVENTS:
                        return

                    if event_type == "problem":
                        self._handle_problem(data_str)
                    elif event_type == "data":
                        for entry in self._parse_data(data_str):
                            yield entry

                elif event_type in _STREAM_END_EVENTS:
                    return

                event_type = None
                data_buffer = []
                continue

            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_buffer.append(line[5:].strip())
            elif not line.startswith(":") and event_type:
                data_buffer.append(line)

    def _parse_data(self, data_str: str) -> list[LogEntry]:
        entries = []
        try:
            json_data = json.loads(data_str)
            if isinstance(json_data, list):
                for item in json_data:
                    entries.append(self._entry_model.model_validate(item))
            else:
                entries.append(self._entry_model.model_validate(json_data))
        except json.JSONDecodeError as e:
            log.warning(f"Failed to parse log entry JSON: {e}")
        except Exception as e:
            log.warning(f"Failed to validate log entry: {e}")
        return entries

    def _handle_problem(self, data_str: str) -> None:
        try:
            problem_data = json.loads(data_str)
            problem = LogProblem.model_validate(problem_data)

            if problem.status == 400:
                raise ValidationError(
                    message=problem.reason,
                    errors=[{"detail": problem.detail}] if problem.detail else None,
                )
            else:
                raise APIError(
                    message=problem.reason,
                    status_code=problem.status,
                    response_body=problem_data,
                )
        except json.JSONDecodeError as e:
            raise APIError(message=f"Invalid problem event: {data_str}") from e


class WorkspaceLogManager(WorkspaceScopedResource):
    """Manager for streaming workspace logs via SSE.

    The unified API takes a :data:`LogTarget`:

    ```python
    async for entry in workspace.logs.stream(StageTarget(LogStage.RUN, step=1)):
        ...
    entries = await workspace.logs.collect(ServerTarget(step=1, server="web"))
    ```
    """

    def _build_endpoint(self, operation: StreamOperation, **kwargs: Any) -> str:
        return operation.endpoint_template.format(id=self.workspace_id, **kwargs)

    def open(self, target: LogTarget, timeout: float | None = None) -> LogStream:
        """Open a log stream for ``target`` as an async context manager."""
        op, params = _resolve_target(target)
        endpoint = self._build_endpoint(op, **params)
        return LogStream(self._http_client, endpoint, op.entry_model, timeout=timeout)

    async def stream(
        self,
        target: LogTarget | LogStage | str,
        step: int | None = None,
        timeout: float | None = 30.0,
    ) -> AsyncIterator[LogEntry]:
        """Stream log entries for ``target`` as they arrive."""
        resolved = self._coerce_target(target, step, "stream")
        async with self.open(resolved, timeout) as stream:
            async for entry in stream:
                yield entry

    async def collect(
        self,
        target: LogTarget | LogStage | str,
        step: int | None = None,
        max_entries: int | None = None,
        timeout: float | None = 30.0,
    ) -> list[LogEntry]:
        """Collect log entries for ``target`` into a list."""
        resolved = self._coerce_target(target, step, "collect")
        entries: list[LogEntry] = []
        try:
            async with self.open(resolved, timeout) as stream:
                async for entry in stream:
                    entries.append(entry)
                    if max_entries and len(entries) >= max_entries:
                        break
        except TimeoutError:
            pass
        return entries

    @staticmethod
    def _coerce_target(
        target: LogTarget | LogStage | str, step: int | None, method: str
    ) -> LogTarget:
        if isinstance(target, StageTarget | ServerTarget | ReplicaTarget):
            return target
        _deprecated(f"{method}(stage, step)", f"{method}(StageTarget(stage, step))")
        return StageTarget(stage=target, step=step if step is not None else 0)

    # ------------------------------------------------------------------
    # Deprecated aliases (kept for backwards compatibility)
    # ------------------------------------------------------------------

    def open_stream(
        self, stage: LogStage | str, step: int, timeout: float | None = None
    ) -> LogStream:
        """Deprecated: use :meth:`open` with a :class:`StageTarget`."""
        _deprecated("open_stream", "open(StageTarget(...))")
        return self.open(StageTarget(stage=stage, step=step), timeout=timeout)

    def open_server_stream(
        self, step: int, server: str, timeout: float | None = None
    ) -> LogStream:
        """Deprecated: use :meth:`open` with a :class:`ServerTarget`."""
        _deprecated("open_server_stream", "open(ServerTarget(...))")
        return self.open(ServerTarget(step=step, server=server), timeout=timeout)

    def open_replica_stream(
        self, step: int, replica: str, timeout: float | None = None
    ) -> LogStream:
        """Deprecated: use :meth:`open` with a :class:`ReplicaTarget`."""
        _deprecated("open_replica_stream", "open(ReplicaTarget(...))")
        return self.open(ReplicaTarget(step=step, replica=replica), timeout=timeout)

    async def stream_server(
        self, step: int, server: str, timeout: float | None = None
    ) -> AsyncIterator[LogEntry]:
        """Deprecated: use :meth:`stream` with a :class:`ServerTarget`."""
        _deprecated("stream_server", "stream(ServerTarget(...))")
        async for entry in self.stream(
            ServerTarget(step=step, server=server), timeout=timeout
        ):
            yield entry

    async def stream_replica(
        self, step: int, replica: str, timeout: float | None = None
    ) -> AsyncIterator[LogEntry]:
        """Deprecated: use :meth:`stream` with a :class:`ReplicaTarget`."""
        _deprecated("stream_replica", "stream(ReplicaTarget(...))")
        async for entry in self.stream(
            ReplicaTarget(step=step, replica=replica), timeout=timeout
        ):
            yield entry

    async def collect_server(
        self,
        step: int,
        server: str,
        max_entries: int | None = None,
        timeout: float | None = 30.0,
    ) -> list[LogEntry]:
        """Deprecated: use :meth:`collect` with a :class:`ServerTarget`."""
        _deprecated("collect_server", "collect(ServerTarget(...))")
        return await self.collect(
            ServerTarget(step=step, server=server),
            max_entries=max_entries,
            timeout=timeout,
        )

    async def collect_replica(
        self,
        step: int,
        replica: str,
        max_entries: int | None = None,
        timeout: float | None = 30.0,
    ) -> list[LogEntry]:
        """Deprecated: use :meth:`collect` with a :class:`ReplicaTarget`."""
        _deprecated("collect_replica", "collect(ReplicaTarget(...))")
        return await self.collect(
            ReplicaTarget(step=step, replica=replica),
            max_entries=max_entries,
            timeout=timeout,
        )
