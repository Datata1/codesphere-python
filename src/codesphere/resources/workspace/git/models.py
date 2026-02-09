from __future__ import annotations

import logging
from typing import Optional

from ....core.handler import _APIOperationExecutor
from ....http_client import APIHttpClient
from .operations import (
    _GET_HEAD_OP,
    _PULL_OP,
    _PULL_WITH_REMOTE_AND_BRANCH_OP,
    _PULL_WITH_REMOTE_OP,
)
from .schema import GitHead

log = logging.getLogger(__name__)


class WorkspaceGitManager(_APIOperationExecutor):
    """Manager for git operations on a workspace."""

    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        self._http_client = http_client
        self._workspace_id = workspace_id
        self.id = workspace_id

    async def get_head(self) -> GitHead:
        return await self._execute_operation(_GET_HEAD_OP)

    async def pull(
        self,
        remote: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> None:
        if remote is not None and branch is not None:
            await self._execute_operation(
                _PULL_WITH_REMOTE_AND_BRANCH_OP, remote=remote, branch=branch
            )
        elif remote is not None:
            await self._execute_operation(_PULL_WITH_REMOTE_OP, remote=remote)
        else:
            await self._execute_operation(_PULL_OP)
