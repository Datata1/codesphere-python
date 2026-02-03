from __future__ import annotations
from functools import cached_property
import logging
from pydantic import Field
from typing import Dict, Optional, List

from .command_schemas import CommandInput, CommandOutput, WorkspaceStatus
from .envVars import EnvVar, WorkspaceEnvVarManager
from ...core.base import CamelModel
from ...core import _APIOperationExecutor, AsyncCallable
from ...http_client import APIHttpClient
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


class Workspace(WorkspaceBase, _APIOperationExecutor):
    update_op: AsyncCallable[None] = Field(
        default=None,
        exclude=True,
    )

    async def update(self, data: WorkspaceUpdate) -> None:
        from .operations import _UPDATE_OP

        await self._execute_operation(_UPDATE_OP, data=data)
        update_model_fields(target=self, source=data)

    delete_op: AsyncCallable[None] = Field(
        default=None,
        exclude=True,
    )

    async def delete(self) -> None:
        from .operations import _DELETE_OP

        await self._execute_operation(_DELETE_OP)

    get_status_op: AsyncCallable[WorkspaceStatus] = Field(
        default=None,
        exclude=True,
    )

    async def get_status(self) -> WorkspaceStatus:
        from .operations import _GET_STATUS_OP

        return await self._execute_operation(_GET_STATUS_OP)

    execute_command_op: AsyncCallable[CommandOutput] = Field(
        default=None,
        exclude=True,
    )

    async def execute_command(
        self, command: str, env: Optional[Dict[str, str]] = None
    ) -> CommandOutput:
        from .operations import _EXECUTE_COMMAND_OP

        command_data = CommandInput(command=command, env=env)
        return await self._execute_operation(_EXECUTE_COMMAND_OP, data=command_data)

    @cached_property
    def env_vars(self) -> WorkspaceEnvVarManager:
        if self._http_client is None or not isinstance(
            self._http_client, APIHttpClient
        ):
            raise RuntimeError("Cannot access 'env_vars' on a detached model.")
        return WorkspaceEnvVarManager(
            http_client=self._http_client, workspace_id=self.id
        )
