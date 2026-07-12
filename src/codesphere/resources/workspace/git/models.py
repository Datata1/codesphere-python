from __future__ import annotations

import logging

from ....core.base import ResourceBase
from ....http_client import APIHttpClient
from .operations import (
    _GET_HEAD_OP,
    _PULL_OP,
    _PULL_WITH_REMOTE_AND_BRANCH_OP,
    _PULL_WITH_REMOTE_OP,
)
from .schema import GitHead

log = logging.getLogger(__name__)


class WorkspaceGitManager(ResourceBase):
    """Manager for git operations on a workspace."""

    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        super().__init__(http_client)
        self._workspace_id = workspace_id
        self.id = workspace_id

    async def get_head(self) -> GitHead:
        return await self._execute(_GET_HEAD_OP, id=self.id)

    async def pull(
        self,
        remote: str | None = None,
        branch: str | None = None,
    ) -> None:
        if remote is not None and branch is not None:
            await self._execute(
                _PULL_WITH_REMOTE_AND_BRANCH_OP,
                id=self.id,
                remote=remote,
                branch=branch,
            )
        elif remote is not None:
            await self._execute(_PULL_WITH_REMOTE_OP, id=self.id, remote=remote)
        else:
            await self._execute(_PULL_OP, id=self.id)
