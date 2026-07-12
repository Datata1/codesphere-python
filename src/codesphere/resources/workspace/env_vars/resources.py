from __future__ import annotations

import logging
from collections.abc import Sequence

from ....core.base import ResourceList, WorkspaceScopedResource
from .operations import _BULK_DELETE_OP, _BULK_SET_OP, _GET_OP
from .schemas import EnvVar

log = logging.getLogger(__name__)


class WorkspaceEnvVarManager(WorkspaceScopedResource):
    async def get(self) -> ResourceList[EnvVar]:
        return await self._execute(_GET_OP, id=self.workspace_id)

    async def set(
        self, env_vars: ResourceList[EnvVar] | Sequence[EnvVar | dict[str, str]]
    ) -> None:
        payload = ResourceList[EnvVar].model_validate(env_vars)
        await self._execute(_BULK_SET_OP, id=self.workspace_id, data=payload)

    async def delete(
        self, items: Sequence[str | EnvVar | dict[str, str]] | ResourceList[EnvVar]
    ) -> None:
        if not items:
            return
        payload: list[str] = []

        for item in items:
            if isinstance(item, str):
                payload.append(item)
            elif isinstance(item, EnvVar):
                payload.append(item.name)
            elif isinstance(item, dict) and "name" in item:
                payload.append(item["name"])

        if payload:
            await self._execute(_BULK_DELETE_OP, id=self.workspace_id, data=payload)
