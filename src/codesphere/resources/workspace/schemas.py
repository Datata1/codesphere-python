from __future__ import annotations

import asyncio
import logging
from functools import cached_property

from ...core.base import BoundModel, CamelModel
from ...utils import update_model_fields
from .envVars import EnvVar, WorkspaceEnvVarManager
from .git import WorkspaceGitManager
from .landscape import WorkspaceLandscapeManager
from .logs import WorkspaceLogManager

log = logging.getLogger(__name__)


class WorkspaceCreate(CamelModel):
    team_id: int
    name: str
    plan_id: int
    base_image: str | None = None
    is_private_repo: bool = True
    replicas: int = 1
    git_url: str | None = None
    initial_branch: str | None = None
    clone_depth: int | None = None
    source_workspace_id: int | None = None
    welcome_message: str | None = None
    vpn_config: str | None = None
    restricted: bool | None = None
    env: list[EnvVar] | None = None


class WorkspaceBase(CamelModel):
    id: int
    team_id: int
    name: str
    plan_id: int
    is_private_repo: bool
    replicas: int
    base_image: str | None = None
    data_center_id: int
    user_id: int
    git_url: str | None = None
    initial_branch: str | None = None
    source_workspace_id: int | None = None
    welcome_message: str | None = None
    vpn_config: str | None = None
    restricted: bool


class WorkspaceUpdate(CamelModel):
    plan_id: int | None = None
    base_image: str | None = None
    name: str | None = None
    replicas: int | None = None
    vpn_config: str | None = None
    restricted: bool | None = None


class CommandInput(CamelModel):
    command: str
    env: dict[str, str] | None = None


class CommandOutput(CamelModel):
    command: str
    working_dir: str
    output: str
    error: str


class WorkspaceStatus(CamelModel):
    is_running: bool


class Workspace(WorkspaceBase, BoundModel):
    async def update(self, data: WorkspaceUpdate) -> None:
        from .operations import _UPDATE_OP

        await self._execute(_UPDATE_OP, id=self.id, data=data)
        update_model_fields(target=self, source=data)

    async def delete(self) -> None:
        from .operations import _DELETE_OP

        await self._execute(_DELETE_OP, id=self.id)

    async def get_status(self) -> WorkspaceStatus:
        from .operations import _GET_STATUS_OP

        return await self._execute(_GET_STATUS_OP, id=self.id)

    async def wait_until_running(
        self,
        *,
        timeout: float = 300.0,
        poll_interval: float = 5.0,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be greater than 0")

        elapsed = 0.0
        while elapsed < timeout:
            status = await self.get_status()
            if status.is_running:
                log.debug("Workspace %s is now running.", self.id)
                return
            log.debug(
                "Workspace %s not running yet, waiting %ss... (elapsed: %.1fs)",
                self.id,
                poll_interval,
                elapsed,
            )
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(
            f"Workspace {self.id} did not reach running state within {timeout} seconds."
        )

    async def execute_command(
        self, command: str, env: dict[str, str] | None = None
    ) -> CommandOutput:
        from .operations import _EXECUTE_COMMAND_OP

        command_data = CommandInput(command=command, env=env)
        return await self._execute(_EXECUTE_COMMAND_OP, id=self.id, data=command_data)

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
