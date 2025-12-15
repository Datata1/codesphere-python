from __future__ import annotations
from functools import cached_property
import logging
from pydantic import Field
from typing import Dict, Optional, List

from .operations import _DELETE_OP, _EXECUTE_COMMAND_OP, _GET_STATUS_OP, _UPDATE_OP
from .envVars import EnvVar, WorkspaceEnvVarManager
from ...core.base import CamelModel
from ...core import _APIOperationExecutor, AsyncCallable
from ...utils import update_model_fields

log = logging.getLogger(__name__)


class WorkspaceCreate(CamelModel):
    team_id: int
    name: str
    plan_id: int
    base_image: Optional[str] = None
    is_private_repo: bool = True
    replicas: int = 1
    git_url: Optional[str] = None
    initial_branch: Optional[str] = None
    clone_depth: Optional[int] = None
    source_workspace_id: Optional[int] = None
    welcome_message: Optional[str] = None
    vpn_config: Optional[str] = None
    restricted: Optional[bool] = None
    env: Optional[List[EnvVar]] = None


class WorkspaceBase(CamelModel):
    id: int
    team_id: int
    name: str
    plan_id: int
    is_private_repo: bool
    replicas: int
    base_image: Optional[str] = None
    data_center_id: int
    user_id: int
    git_url: Optional[str] = None
    initial_branch: Optional[str] = None
    source_workspace_id: Optional[int] = None
    welcome_message: Optional[str] = None
    vpn_config: Optional[str] = None
    restricted: bool


class WorkspaceUpdate(CamelModel):
    plan_id: Optional[int] = None
    base_image: Optional[str] = None
    name: Optional[str] = None
    replicas: Optional[int] = None
    vpn_config: Optional[str] = None
    restricted: Optional[bool] = None


class WorkspaceStatus(CamelModel):
    is_running: bool


class CommandInput(CamelModel):
    command: str
    env: Optional[Dict[str, str]] = None


class CommandOutput(CamelModel):
    command: str
    working_dir: str
    output: str
    error: str


class Workspace(WorkspaceBase, _APIOperationExecutor):
    update_op: AsyncCallable[None] = Field(
        default=_UPDATE_OP,
        exclude=True,
    )

    async def update(self, data: WorkspaceUpdate) -> None:
        await self.update_op(data=data)
        update_model_fields(target=self, source=data)

    delete_op: AsyncCallable[None] = Field(
        default=_DELETE_OP,
        exclude=True,
    )

    async def delete(self) -> None:
        await self.delete_op()

    get_status_op: AsyncCallable[WorkspaceStatus] = Field(
        default=_GET_STATUS_OP,
        exclude=True,
    )

    async def get_status(self) -> WorkspaceStatus:
        return await self.get_status_op()

    execute_command_op: AsyncCallable[CommandOutput] = Field(
        default=_EXECUTE_COMMAND_OP,
        exclude=True,
    )

    async def execute_command(
        self, command: str, env: Optional[Dict[str, str]] = None
    ) -> CommandOutput:
        command_data = CommandInput(command=command, env=env)
        return await self.execute_command_op(data=command_data)

    @cached_property
    def env_vars(self) -> WorkspaceEnvVarManager:
        if not self._http_client:
            raise RuntimeError("Cannot access 'env_vars' on a detached model.")
        return WorkspaceEnvVarManager(
            http_client=self._http_client, workspace_id=self.id
        )
