from __future__ import annotations
from pydantic import BaseModel, PrivateAttr, parse_obj_as
from typing import Optional, List, TYPE_CHECKING, Union, Dict

if TYPE_CHECKING:
    from ...client import APIHttpClient


class EnvVarPair(BaseModel):
    name: str
    value: str


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
    env: Optional[List[EnvVarPair]] = None


# Defines the request body for PATCH /workspaces/{workspaceId}
class WorkspaceUpdate(BaseModel):
    planId: Optional[int] = None
    baseImage: Optional[str] = None
    name: Optional[str] = None
    replicas: Optional[int] = None
    vpnConfig: Optional[str] = None
    restricted: Optional[bool] = None


# Defines the response from GET /workspaces/{workspaceId}/status
class WorkspaceStatus(BaseModel):
    isRunning: bool


# This is the main model for a workspace, returned by GET, POST, and LIST
class Workspace(BaseModel):
    _http_client: Optional[APIHttpClient] = PrivateAttr(default=None)

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

    async def update(self, data: WorkspaceUpdate) -> None:
        """Updates this workspace with new data."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")

        await self._http_client.patch(
            f"/workspaces/{self.id}", json=data.model_dump(exclude_unset=True)
        )
        # Optionally, update the local object's state
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(self, key, value)

    async def delete(self) -> None:
        """Deletes this workspace."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")
        await self._http_client.delete(f"/workspaces/{self.id}")

    async def get_status(self) -> WorkspaceStatus:
        """Gets the running status of this workspace."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")

        response = await self._http_client.get(f"/workspaces/{self.id}/status")
        return WorkspaceStatus.model_validate(response.json())

    async def get_env_vars(self) -> list[EnvVarPair]:
        """Fetches all environment variables for this workspace."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")

        response = await self._http_client.get(f"/workspaces/{self.id}/env-vars")
        return parse_obj_as(list[EnvVarPair], response.json())

    async def set_env_vars(
        self, env_vars: Union[List[EnvVarPair], List[Dict[str, str]]]
    ) -> None:
        """
        Sets or updates environment variables for this workspace.
        This operation replaces all existing variables with the provided list.
        Accepts either a list of EnvVarPair models or a list of dictionaries.
        """
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")

        json_payload = []
        if env_vars and isinstance(env_vars[0], EnvVarPair):
            json_payload = [var.model_dump() for var in env_vars]
        else:
            json_payload = env_vars

        await self._http_client.put(
            f"/workspaces/{self.id}/env-vars", json=json_payload
        )

    async def delete_env_vars(
        self, var_names: Union[List[str], List[EnvVarPair]]
    ) -> None:
        """Deletes specific environment variables from this workspace."""
        if not self._http_client:
            raise RuntimeError("Cannot make API calls on a detached model.")

        payload = []
        if var_names and isinstance(var_names[0], EnvVarPair):
            payload = [var.name for var in var_names]
        else:
            payload = var_names

        await self._http_client.delete(f"/workspaces/{self.id}/env-vars", json=payload)

    async def execute_command():
        pass

    async def git_pull():
        pass

    async def git_head():
        pass
