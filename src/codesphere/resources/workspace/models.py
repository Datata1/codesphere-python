from __future__ import annotations
from functools import cached_property
import logging
from pydantic import BaseModel, Field
from typing import Dict, Optional, List

from ...utils import update_model_fields
from ...core import _APIOperationExecutor, APIOperation, AsyncCallable
from .envVars import EnvVar, WorkspaceEnvVarManager

log = logging.getLogger(__name__)


class WorkspaceCreate(BaseModel):
    teamId: int
    name: str
    planId: int
    baseImage: Optional[str] = None
    isPrivateRepo: bool = True
    replicas: int = 1
    gitUrl: Optional[str] = None
    initialBranch: Optional[str] = None
    cloneDepth: Optional[int] = None
    sourceWorkspaceId: Optional[int] = None
    welcomeMessage: Optional[str] = None
    vpnConfig: Optional[str] = None
    restricted: Optional[bool] = None
    env: Optional[List[EnvVar]] = None


class WorkspaceBase(BaseModel):
    id: int
    teamId: int
    name: str
    planId: int
    isPrivateRepo: bool
    replicas: int
    baseImage: Optional[str] = None
    dataCenterId: int
    userId: int
    gitUrl: Optional[str] = None
    initialBranch: Optional[str] = None
    sourceWorkspaceId: Optional[int] = None
    welcomeMessage: Optional[str] = None
    vpnConfig: Optional[str] = None
    restricted: bool


class WorkspaceUpdate(BaseModel):
    planId: Optional[int] = None
    baseImage: Optional[str] = None
    name: Optional[str] = None
    replicas: Optional[int] = None
    vpnConfig: Optional[str] = None
    restricted: Optional[bool] = None


class WorkspaceStatus(BaseModel):
    isRunning: bool


class CommandInput(BaseModel):
    command: str
    env: Optional[Dict[str, str]] = None


class CommandOutput(BaseModel):
    command: str
    workingDir: str
    output: str
    error: str


class Workspace(WorkspaceBase, _APIOperationExecutor):
    update_op: AsyncCallable[None] = Field(
        default=APIOperation(
            method="PATCH",
            endpoint_template="/workspaces/{id}",
            response_model=None,
        ),
        exclude=True,
    )

    delete_op: AsyncCallable[None] = Field(
        default=APIOperation(
            method="DELETE",
            endpoint_template="/workspaces/{id}",
            response_model=None,
        ),
        exclude=True,
    )

    get_status_op: AsyncCallable[WorkspaceStatus] = Field(
        default=APIOperation(
            method="GET",
            endpoint_template="/workspaces/{id}/status",
            response_model=WorkspaceStatus,
        ),
        exclude=True,
    )

    execute_command_op: AsyncCallable[CommandOutput] = Field(
        default=APIOperation(
            method="POST",
            endpoint_template="/workspaces/{id}/execute",
            input_model=CommandInput,
            response_model=CommandOutput,
        ),
        exclude=True,
    )

    async def update(self, data: WorkspaceUpdate) -> None:
        """
        Updates this workspace with new data and refreshes the
        local object state.

        Args:
            data (WorkspaceUpdate): The payload with fields to update.
        """
        await self.update_op(data=data)
        update_model_fields(target=self, source=data)

    async def delete(self) -> None:
        """Deletes this workspace."""
        await self.delete_op()

    async def get_status(self) -> WorkspaceStatus:
        """Gets the running status of this workspace."""
        return await self.get_status_op()

    async def execute_command(
        self, command: str, env: Optional[Dict[str, str]] = None
    ) -> CommandOutput:
        command_data = CommandInput(command=command, env=env)
        return await self.execute_command_op(data=command_data)

    @cached_property
    def env_vars(self) -> WorkspaceEnvVarManager:
        """
        Provides access to the Environment Variable manager for this workspace.

        Usage:
            >>> await workspace.env_vars.get()
            >>> await workspace.env_vars.set([{"name": "KEY", "value": "VALUE"}])
        """
        if not self._http_client:
            raise RuntimeError("Cannot access 'env_vars' on a detached model.")
        return WorkspaceEnvVarManager(
            http_client=self._http_client, workspace_id=self.id
        )
