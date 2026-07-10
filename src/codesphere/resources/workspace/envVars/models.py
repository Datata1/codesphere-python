from __future__ import annotations

import logging

from ....core.base import ResourceList
from ....core.handler import _APIOperationExecutor
from ....http_client import APIHttpClient
from .operations import _BULK_DELETE_OP, _BULK_SET_OP, _GET_OP
from .schemas import EnvVar

log = logging.getLogger(__name__)


class WorkspaceEnvVarManager(_APIOperationExecutor):
    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        self._http_client = http_client
        self._workspace_id = workspace_id
        self.id = workspace_id

    async def get(self) -> list[EnvVar]:
        return await self._execute_operation(_GET_OP)

    async def set(self, env_vars: ResourceList[EnvVar] | list[dict[str, str]]) -> None:
        payload = ResourceList[EnvVar].model_validate(env_vars)
        await self._execute_operation(_BULK_SET_OP, data=payload.model_dump())

    async def delete(self, items: list[str] | ResourceList[EnvVar]) -> None:
        if not items:
            return
        payload: list[str] = []

        for item in items:
            if isinstance(item, str):
                payload.append(item)
            elif hasattr(item, "name"):
                payload.append(item.name)
            elif isinstance(item, dict) and "name" in item:
                payload.append(item["name"])

        if payload:
            await self._execute_operation(_BULK_DELETE_OP, data=payload)
