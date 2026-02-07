from typing import List
from pydantic import Field

from ...core.base import ResourceList
from ...core.operations import AsyncCallable
from .operations import (
    _CREATE_OP,
    _GET_OP,
    _LIST_BY_TEAM_OP,
)

from ...core import ResourceBase
from .schemas import Workspace, WorkspaceCreate


class WorkspacesResource(ResourceBase):
    list_by_team_op: AsyncCallable[ResourceList[Workspace]] = Field(
        default=_LIST_BY_TEAM_OP, exclude=True
    )

    async def list(self, team_id: int) -> List[Workspace]:
        result = await self.list_by_team_op(team_id=team_id)
        return result.root

    get_op: AsyncCallable[Workspace] = Field(default=_GET_OP, exclude=True)

    async def get(self, workspace_id: int) -> Workspace:
        return await self.get_op(workspace_id=workspace_id)

    create_op: AsyncCallable[Workspace] = Field(default=_CREATE_OP, exclude=True)

    async def create(self, payload: WorkspaceCreate) -> Workspace:
        return await self.create_op(data=payload)
