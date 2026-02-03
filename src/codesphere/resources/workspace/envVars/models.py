from __future__ import annotations
import logging
from typing import Dict, List, Union
from pydantic import Field

from .schemas import EnvVar
from ....core.base import ResourceList
from ....core.handler import _APIOperationExecutor
from ....core.operations import AsyncCallable
from ....http_client import APIHttpClient

log = logging.getLogger(__name__)


class WorkspaceEnvVarManager(_APIOperationExecutor):
    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        self._http_client = http_client
        self._workspace_id = workspace_id
        self.id = workspace_id

    get_all_op: AsyncCallable[ResourceList[EnvVar]] = Field(
        default=None,
        exclude=True,
    )

    async def get(self) -> List[EnvVar]:
        from .operations import _GET_OP

        return await self._execute_operation(_GET_OP)

    bulk_set_op: AsyncCallable[None] = Field(
        default=None,
        exclude=True,
    )

    async def set(
        self, env_vars: Union[ResourceList[EnvVar], List[Dict[str, str]]]
    ) -> None:
        from .operations import _BULK_SET_OP

        payload = ResourceList[EnvVar].model_validate(env_vars)
        await self._execute_operation(_BULK_SET_OP, data=payload.model_dump())

    bulk_delete_op: AsyncCallable[None] = Field(
        default=None,
        exclude=True,
    )

    async def delete(self, items: Union[List[str], ResourceList[EnvVar]]) -> None:
        if not items:
            return

        from .operations import _BULK_DELETE_OP

        payload: List[str] = []

        for item in items:
            if isinstance(item, str):
                payload.append(item)
            elif hasattr(item, "name"):
                payload.append(item.name)
            elif isinstance(item, dict) and "name" in item:
                payload.append(item["name"])

        if payload:
            await self._execute_operation(_BULK_DELETE_OP, data=payload)
