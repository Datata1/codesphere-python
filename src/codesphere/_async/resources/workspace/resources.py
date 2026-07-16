import httpx

from codesphere.exceptions import ValidationError

from ...core import ResourceBase
from .operations import (
    _CREATE_OP,
    _GET_OP,
    _LIST_BY_TEAM_OP,
)
from .schemas import Workspace, WorkspaceCreate


class WorkspacesResource(ResourceBase):
    async def list(
        self, team_id: int, *, timeout: httpx.Timeout | float | None = None
    ) -> list[Workspace]:
        if team_id <= 0:
            raise ValidationError("team_id must be a positive integer")
        result = await self._execute(_LIST_BY_TEAM_OP, team_id=team_id, timeout=timeout)
        return result.root

    async def get(
        self, workspace_id: int, *, timeout: httpx.Timeout | float | None = None
    ) -> Workspace:
        if workspace_id <= 0:
            raise ValidationError("workspace_id must be a positive integer")
        return await self._execute(_GET_OP, workspace_id=workspace_id, timeout=timeout)

    async def create(
        self, payload: WorkspaceCreate, *, timeout: httpx.Timeout | float | None = None
    ) -> Workspace:
        return await self._execute(_CREATE_OP, data=payload, timeout=timeout)
