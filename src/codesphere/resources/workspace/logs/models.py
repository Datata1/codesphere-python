from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Optional, Union

import httpx

from ....exceptions import APIError, ValidationError
from ....http_client import APIHttpClient
from .schemas import LogEntry, LogProblem, LogStage

log = logging.getLogger(__name__)


class WorkspaceLogManager:
    """Manager for streaming workspace logs via SSE.

    Provides async iterators for streaming logs from different pipeline stages
    and Multi Server Deployment servers/replicas.

    Example:
        ```python
        # Stream prepare stage logs (with timeout for completed stages)
        async for entry in workspace.logs.stream(stage=LogStage.PREPARE, step=1, timeout=30.0):
            print(entry.message)

        # Stream run logs for a specific server (no timeout for live streams)
        async for entry in workspace.logs.stream_server(step=1, server="web"):
            print(entry.message)

        # Collect all logs at once
        logs = await workspace.logs.collect(stage=LogStage.TEST, step=1)
        for entry in logs:
            print(entry.message)
        ```
    """

    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        self._http_client = http_client
        self._workspace_id = workspace_id

    async def stream(
        self,
        stage: Union[LogStage, str],
        step: int,
        timeout: Optional[float] = 30.0,
    ) -> AsyncIterator[LogEntry]:
        """Stream logs for a given stage and step.

        Args:
            stage: The pipeline stage ('prepare', 'test', or 'run').
                   For 'run' stage of Multi Server Deployments, use
                   stream_server() or stream_replica() instead.
            step: The step number within the stage.
            timeout: Maximum seconds to wait for the stream. Default 30s.
                     Use None for no timeout (for live/running stages).

        Yields:
            LogEntry objects as they arrive from the SSE stream.

        Raises:
            ValidationError: If the workspace is not running or parameters are invalid.
            APIError: For other API errors.
            asyncio.TimeoutError: If timeout is reached.
        """
        if isinstance(stage, LogStage):
            stage = stage.value

        endpoint = f"/workspaces/{self._workspace_id}/logs/{stage}/{step}"
        async for entry in self._stream_logs(endpoint, timeout=timeout):
            yield entry

    async def stream_server(
        self,
        step: int,
        server: str,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[LogEntry]:
        """Stream run logs for a specific server in a Multi Server Deployment.

        Args:
            step: The step number.
            server: The server name.
            timeout: Maximum seconds to wait. Default None (no timeout).

        Yields:
            LogEntry objects as they arrive from the SSE stream.

        Raises:
            ValidationError: If the workspace is not running or parameters are invalid.
            APIError: For other API errors.
        """
        endpoint = f"/workspaces/{self._workspace_id}/logs/run/{step}/server/{server}"
        async for entry in self._stream_logs(endpoint, timeout=timeout):
            yield entry

    async def stream_replica(
        self,
        step: int,
        replica: str,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[LogEntry]:
        """Stream run logs for a specific replica in a Multi Server Deployment.

        Args:
            step: The step number.
            replica: The replica identifier.
            timeout: Maximum seconds to wait. Default None (no timeout).

        Yields:
            LogEntry objects as they arrive from the SSE stream.

        Raises:
            ValidationError: If the workspace is not running or parameters are invalid.
            APIError: For other API errors.
        """
        endpoint = f"/workspaces/{self._workspace_id}/logs/run/{step}/replica/{replica}"
        async for entry in self._stream_logs(endpoint, timeout=timeout):
            yield entry

    async def collect(
        self,
        stage: Union[LogStage, str],
        step: int,
        max_entries: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> list[LogEntry]:
        """Collect all logs for a stage and step into a list.

        Args:
            stage: The pipeline stage ('prepare', 'test', or 'run').
            step: The step number within the stage.
            max_entries: Maximum number of entries to collect (None for unlimited).
            timeout: Maximum seconds to collect. Default 30s.

        Returns:
            List of LogEntry objects.
        """
        entries: list[LogEntry] = []
        count = 0
        try:
            async for entry in self.stream(stage, step, timeout=timeout):
                entries.append(entry)
                count += 1
                if max_entries and count >= max_entries:
                    break
        except asyncio.TimeoutError:
            log.debug(f"Log collection timed out after {count} entries")
        return entries

    async def collect_server(
        self,
        step: int,
        server: str,
        max_entries: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> list[LogEntry]:
        """Collect all logs for a server into a list.

        Args:
            step: The step number.
            server: The server name.
            max_entries: Maximum number of entries to collect (None for unlimited).
            timeout: Maximum seconds to collect. Default 30s.

        Returns:
            List of LogEntry objects.
        """
        entries: list[LogEntry] = []
        count = 0
        try:
            async for entry in self.stream_server(step, server, timeout=timeout):
                entries.append(entry)
                count += 1
                if max_entries and count >= max_entries:
                    break
        except asyncio.TimeoutError:
            log.debug(f"Server log collection timed out after {count} entries")
        return entries

    async def collect_replica(
        self,
        step: int,
        replica: str,
        max_entries: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> list[LogEntry]:
        """Collect all logs for a replica into a list.

        Args:
            step: The step number.
            replica: The replica identifier.
            max_entries: Maximum number of entries to collect (None for unlimited).
            timeout: Maximum seconds to collect. Default 30s.

        Returns:
            List of LogEntry objects.
        """
        entries: list[LogEntry] = []
        count = 0
        try:
            async for entry in self.stream_replica(step, replica, timeout=timeout):
                entries.append(entry)
                count += 1
                if max_entries and count >= max_entries:
                    break
        except asyncio.TimeoutError:
            log.debug(f"Replica log collection timed out after {count} entries")
        return entries

    async def _stream_logs(
        self, endpoint: str, timeout: Optional[float] = None
    ) -> AsyncIterator[LogEntry]:
        """Internal method to stream SSE logs from an endpoint.

        Args:
            endpoint: The API endpoint to stream from.
            timeout: Maximum seconds to stream. None for no timeout.

        Yields:
            LogEntry objects parsed from SSE events.
        """
        client = self._http_client._get_client()
        headers = {"Accept": "text/event-stream"}

        log.debug(f"Opening SSE stream: GET {endpoint} (timeout={timeout})")

        async def _do_stream() -> AsyncIterator[LogEntry]:
            async with client.stream(
                "GET",
                endpoint,
                headers=headers,
                timeout=httpx.Timeout(5.0, read=None),
            ) as response:
                if not response.is_success:
                    await response.aread()
                    self._handle_error_response(response)

                async for entry in self._parse_sse_stream(response):
                    yield entry

        if timeout is not None:
            async with asyncio.timeout(timeout):
                async for entry in _do_stream():
                    yield entry
        else:
            async for entry in _do_stream():
                yield entry

    async def _parse_sse_stream(
        self, response: httpx.Response
    ) -> AsyncIterator[LogEntry]:
        """Parse SSE events from the response stream.

        Args:
            response: The streaming httpx Response.

        Yields:
            LogEntry objects from 'data' events.

        Raises:
            ValidationError: If a 'problem' event indicates validation issues.
            APIError: If a 'problem' event indicates other API errors.
        """
        event_type: Optional[str] = None
        data_buffer: list[str] = []

        async for line in response.aiter_lines():
            line = line.strip()

            if not line:
                # Empty line = end of event
                if event_type and data_buffer:
                    data_str = "\n".join(data_buffer)

                    # Handle end/close events - stop streaming
                    if event_type in ("end", "close", "done", "complete"):
                        log.debug(f"Received {event_type} event, closing stream")
                        return

                    # Handle problem events first (raises exception)
                    if event_type == "problem":
                        await self._process_sse_event(event_type, data_str)
                    elif event_type == "data":
                        try:
                            json_data = json.loads(data_str)
                            # API can return a single entry or an array of entries
                            if isinstance(json_data, list):
                                for item in json_data:
                                    yield LogEntry.model_validate(item)
                            else:
                                yield LogEntry.model_validate(json_data)
                        except json.JSONDecodeError as e:
                            log.warning(f"Failed to parse log entry JSON: {e}")
                        except Exception as e:
                            log.warning(f"Failed to validate log entry: {e}")
                elif event_type in ("end", "close", "done", "complete"):
                    # End event with no data
                    log.debug(f"Received {event_type} event, closing stream")
                    return

                event_type = None
                data_buffer = []
                continue

            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_buffer.append(line[5:].strip())
            elif line.startswith(":"):
                # SSE comment - ignore
                pass
            else:
                # Some SSE implementations send data without "data:" prefix
                if event_type:
                    data_buffer.append(line)

    async def _process_sse_event(self, event_type: str, data: str) -> None:
        """Process an SSE event and raise exceptions for problem events.

        Args:
            event_type: The event type ('data' or 'problem').
            data: The JSON data from the event.

        Raises:
            ValidationError: For 400 status problems.
            APIError: For other problem statuses.
        """
        if event_type == "problem":
            try:
                problem_data = json.loads(data)
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
                raise APIError(message=f"Invalid problem event: {data}")

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle non-success HTTP responses.

        Args:
            response: The failed httpx Response.

        Raises:
            Appropriate exception based on status code.
        """
        from ....exceptions import raise_for_status

        raise_for_status(response)
