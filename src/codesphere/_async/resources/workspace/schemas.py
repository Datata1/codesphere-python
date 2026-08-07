from __future__ import annotations

import asyncio
import logging
import time
from functools import cached_property

import httpx

from codesphere.models.workspace import (
    CommandInput,
    CommandOutput,
    WorkspaceBase,
    WorkspaceCreate,
    WorkspaceStatus,
    WorkspaceUpdate,
)

from ...core.base import BoundModel
from .env_vars import EnvVar, WorkspaceEnvVarManager
from .git import WorkspaceGitManager
from .landscape import WorkspaceLandscapeManager
from .logs import WorkspaceLogManager

log = logging.getLogger(__name__)

__all__ = [
    "CommandInput",
    "CommandOutput",
    "EnvVar",
    "Workspace",
    "WorkspaceBase",
    "WorkspaceCreate",
    "WorkspaceStatus",
    "WorkspaceUpdate",
]


class Workspace(WorkspaceBase, BoundModel):
    async def update(
        self,
        data: WorkspaceUpdate,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> None:
        """Apply a partial update, then invalidate this instance.

        The PATCH returns no body, and the platform orders writes by
        arrival while this client sees them by response, so the resulting
        server state is not knowable from here. Rather than write the
        request payload back and risk reporting a value the platform does
        not hold, the instance is marked stale: reads raise
        :class:`~codesphere.StaleModelError` until :meth:`refresh`.
        """
        from .operations import _UPDATE_OP

        await self._execute(_UPDATE_OP, id=self.id, data=data, timeout=timeout)
        self._mark_stale()

    async def refresh(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> Workspace:
        """Re-read this workspace from the server, in place."""
        from .operations import _GET_OP

        fresh = await self._execute(_GET_OP, workspace_id=self.id, timeout=timeout)
        self._adopt(fresh)
        return self

    async def delete(self, *, timeout: httpx.Timeout | float | None = None) -> None:
        from .operations import _DELETE_OP

        await self._execute(_DELETE_OP, id=self.id, timeout=timeout)

    async def get_status(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> WorkspaceStatus:
        from .operations import _GET_STATUS_OP

        return await self._execute(_GET_STATUS_OP, id=self.id, timeout=timeout)

    async def wait_until_running(
        self,
        *,
        timeout: float = 300.0,
        poll_interval: float = 5.0,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than 0")

        # Wall-clock deadline: time spent in the status requests counts
        # against the timeout, not just the sleeps between them.
        deadline = time.monotonic() + timeout
        while True:
            status = await self.get_status()
            if status.is_running:
                log.debug("Workspace %s is now running.", self.id)
                return

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"Workspace {self.id} did not reach running state within "
                    f"{timeout} seconds."
                )
            log.debug(
                "Workspace %s not running yet, waiting %ss... (%.1fs remaining)",
                self.id,
                poll_interval,
                remaining,
            )
            await asyncio.sleep(min(poll_interval, remaining))

    async def execute_command(
        self,
        command: str,
        env: dict[str, str] | None = None,
        *,
        timeout: httpx.Timeout | float | None = None,
    ) -> CommandOutput:
        from .operations import _EXECUTE_COMMAND_OP

        command_data = CommandInput(command=command, env=env)
        return await self._execute(
            _EXECUTE_COMMAND_OP, id=self.id, data=command_data, timeout=timeout
        )

    @cached_property
    def env_vars(self) -> WorkspaceEnvVarManager:
        return WorkspaceEnvVarManager(self._client(), workspace_id=self.id)

    @cached_property
    def landscape(self) -> WorkspaceLandscapeManager:
        """Manager for landscape operations (Multi Server Deployments)."""
        return WorkspaceLandscapeManager(self._client(), workspace_id=self.id)

    @cached_property
    def git(self) -> WorkspaceGitManager:
        """Manager for git operations (head, pull)."""
        return WorkspaceGitManager(self._client(), workspace_id=self.id)

    @cached_property
    def logs(self) -> WorkspaceLogManager:
        """Manager for streaming workspace logs.

        Provides methods to stream or collect logs from pipeline stages
        (prepare, test, run) and Multi Server Deployment servers/replicas.

        Example:
            ```python
            # Stream logs as they arrive
            async for entry in workspace.logs.stream(stage="prepare", step=1):
                print(entry.message)

            # Collect all logs at once
            entries = await workspace.logs.collect(stage="test", step=1)
            ```
        """
        return WorkspaceLogManager(self._client(), workspace_id=self.id)
