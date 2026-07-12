from ...core import ResourceBase
from ...exceptions import ValidationError
from .operations import (
    _CREATE_OP,
    _GET_OP,
    _LIST_BY_TEAM_OP,
)
from .schemas import Workspace, WorkspaceCreate


class WorkspacesResource(ResourceBase):
    async def list(self, team_id: int) -> list[Workspace]:
        if team_id <= 0:
            raise ValidationError("team_id must be a positive integer")
        result = await self._execute(_LIST_BY_TEAM_OP, team_id=team_id)
        return result.root

    async def get(self, workspace_id: int) -> Workspace:
        if workspace_id <= 0:
            raise ValidationError("workspace_id must be a positive integer")
        return await self._execute(_GET_OP, workspace_id=workspace_id)

    async def create(self, payload: WorkspaceCreate) -> Workspace:
        return await self._execute(_CREATE_OP, data=payload)
