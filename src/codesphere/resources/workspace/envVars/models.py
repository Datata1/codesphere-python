from __future__ import annotations
import logging
from typing import Dict, List, Union
from pydantic import BaseModel, Field

from codesphere.core.handler import _APIOperationExecutor
from codesphere.core.operations import APIOperation, AsyncCallable
from codesphere.http_client import APIHttpClient

log = logging.getLogger(__name__)


class EnvVar(BaseModel):
    name: str
    value: str


class WorkspaceEnvVarManager(_APIOperationExecutor):
    """
    Verwaltet die Env Vars für einen *bestimmten* Workspace.
    Wird typischerweise über 'workspace.env_vars' aufgerufen.
    """

    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        self._http_client = http_client
        self._workspace_id = workspace_id
        self.id = workspace_id

    get_all_op: AsyncCallable[List[EnvVar]] = Field(
        default=APIOperation(
            method="GET",
            endpoint_template="/workspaces/{id}/env-vars",
            response_model=List[EnvVar],
        ),
        exclude=True,
    )

    bulk_set_op: AsyncCallable[None] = Field(
        default=APIOperation(
            method="PUT",
            endpoint_template="/workspaces/{id}/env-vars",
            response_model=None,
        ),
        exclude=True,
    )

    bulk_delete_op: AsyncCallable[None] = Field(
        default=APIOperation(
            method="DELETE",
            endpoint_template="/workspaces/{id}/env-vars",
            response_model=None,
        ),
        exclude=True,
    )

    async def get(self) -> List[EnvVar]:
        """Fetches all environment variables for this workspace."""
        env_vars = await self.get_all_op()
        return env_vars

    async def set(self, env_vars: Union[List[EnvVar], List[Dict[str, str]]]) -> None:
        """Sets or updates environment variables for this workspace."""
        json_payload = []
        if env_vars:
            if isinstance(env_vars[0], EnvVar):
                json_payload = [var.model_dump() for var in env_vars]
            else:
                json_payload = env_vars

        await self.bulk_set_op(data=json_payload)

    async def delete(self, var_names: Union[List[str], List[EnvVar]]) -> None:
        """Deletes specific environment variables from this workspace."""
        payload = []
        if var_names:
            if isinstance(var_names[0], EnvVar):
                payload = [var.name for var in var_names]
            else:
                payload = var_names

        await self.bulk_delete_op(data=payload)
