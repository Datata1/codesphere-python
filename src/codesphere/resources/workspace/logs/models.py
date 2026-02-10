from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Optional, Type, Union

import httpx

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


class LogStream:
    """Async context manager for streaming logs via SSE."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        entry_model: Type[LogEntry],
        timeout: Optional[float] = None,
    ):
        self._client = client
        self._endpoint = endpoint
        self._entry_model = entry_model
        self._timeout = timeout
        self._response: Optional[httpx.Response] = None
        self._stream_context = None

    async def __aenter__(self) -> LogStream:
        headers = {"Accept": "text/event-stream"}
        self._stream_context = self._client.stream(
            "GET",
            self._endpoint,
            headers=headers,
            timeout=httpx.Timeout(5.0, read=None),
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
        event_type: Optional[str] = None
        data_buffer: list[str] = []

        async for line in self._response.aiter_lines():
            line = line.strip()

            if not line:
                if event_type and data_buffer:
                    data_str = "\n".join(data_buffer)

                    if event_type in ("end", "close", "done", "complete"):
                        return

                    if event_type == "problem":
                        self._handle_problem(data_str)
                    elif event_type == "data":
                        for entry in self._parse_data(data_str):
                            yield entry

                elif event_type in ("end", "close", "done", "complete"):
                    return

                event_type = None
                data_buffer = []
                continue

            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_buffer.append(line[5:].strip())
            elif not line.startswith(":"):
                if event_type:
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
        except json.JSONDecodeError:
            raise APIError(message=f"Invalid problem event: {data_str}")


class WorkspaceLogManager:
    """Manager for streaming workspace logs via SSE."""

    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        self._http_client = http_client
        self._workspace_id = workspace_id
        self.id = workspace_id

    def _build_endpoint(self, operation: StreamOperation, **kwargs) -> str:
        return operation.endpoint_template.format(id=self._workspace_id, **kwargs)

    def _open_stream(
        self,
        operation: StreamOperation,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> LogStream:
        endpoint = self._build_endpoint(operation, **kwargs)
        return LogStream(
            client=self._http_client._get_client(),
            endpoint=endpoint,
            entry_model=operation.entry_model,
            timeout=timeout,
        )

    def open_stream(
        self,
        stage: Union[LogStage, str],
        step: int,
        timeout: Optional[float] = None,
    ) -> LogStream:
        """Open a log stream as an async context manager."""
        if isinstance(stage, LogStage):
            stage = stage.value
        return self._open_stream(
            _STREAM_STAGE_LOGS_OP, timeout=timeout, stage=stage, step=step
        )

    def open_server_stream(
        self,
        step: int,
        server: str,
        timeout: Optional[float] = None,
    ) -> LogStream:
        """Open a server log stream as an async context manager."""
        return self._open_stream(
            _STREAM_SERVER_LOGS_OP, timeout=timeout, step=step, server=server
        )

    def open_replica_stream(
        self,
        step: int,
        replica: str,
        timeout: Optional[float] = None,
    ) -> LogStream:
        """Open a replica log stream as an async context manager."""
        return self._open_stream(
            _STREAM_REPLICA_LOGS_OP, timeout=timeout, step=step, replica=replica
        )

    async def stream(
        self,
        stage: Union[LogStage, str],
        step: int,
        timeout: Optional[float] = 30.0,
    ) -> AsyncIterator[LogEntry]:
        """Stream logs for a given stage and step."""
        async with self.open_stream(stage, step, timeout) as stream:
            async for entry in stream:
                yield entry

    async def stream_server(
        self,
        step: int,
        server: str,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[LogEntry]:
        """Stream run logs for a specific server."""
        async with self.open_server_stream(step, server, timeout) as stream:
            async for entry in stream:
                yield entry

    async def stream_replica(
        self,
        step: int,
        replica: str,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[LogEntry]:
        """Stream run logs for a specific replica."""
        async with self.open_replica_stream(step, replica, timeout) as stream:
            async for entry in stream:
                yield entry

    async def collect(
        self,
        stage: Union[LogStage, str],
        step: int,
        max_entries: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> list[LogEntry]:
        """Collect all logs for a stage and step into a list."""
        entries: list[LogEntry] = []
        try:
            async with self.open_stream(stage, step, timeout) as stream:
                async for entry in stream:
                    entries.append(entry)
                    if max_entries and len(entries) >= max_entries:
                        break
        except asyncio.TimeoutError:
            pass
        return entries

    async def collect_server(
        self,
        step: int,
        server: str,
        max_entries: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> list[LogEntry]:
        """Collect all logs for a server into a list."""
        entries: list[LogEntry] = []
        try:
            async with self.open_server_stream(step, server, timeout) as stream:
                async for entry in stream:
                    entries.append(entry)
                    if max_entries and len(entries) >= max_entries:
                        break
        except asyncio.TimeoutError:
            pass
        return entries

    async def collect_replica(
        self,
        step: int,
        replica: str,
        max_entries: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> list[LogEntry]:
        """Collect all logs for a replica into a list."""
        entries: list[LogEntry] = []
        try:
            async with self.open_replica_stream(step, replica, timeout) as stream:
                async for entry in stream:
                    entries.append(entry)
                    if max_entries and len(entries) >= max_entries:
                        break
        except asyncio.TimeoutError:
            pass
        return entries
