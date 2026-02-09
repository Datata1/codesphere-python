from typing import AsyncGenerator

import pytest

from codesphere import CodesphereSDK
from codesphere.resources.workspace import Workspace, WorkspaceCreate

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
async def git_workspace(
    session_sdk_client: CodesphereSDK,
    test_team_id: int,
    test_plan_id: int,
) -> AsyncGenerator[Workspace, None]:
    payload = WorkspaceCreate(
        team_id=test_team_id,
        name="sdk-git-integration-test",
        plan_id=test_plan_id,
        git_url="https://github.com/octocat/Hello-World.git",
    )

    workspace = await session_sdk_client.workspaces.create(payload=payload)

    try:
        await workspace.wait_until_running(timeout=120.0)
        yield workspace
    finally:
        try:
            await workspace.delete()
        except Exception:
            pass


class TestGitIntegration:
    @pytest.mark.asyncio
    async def test_get_head(self, git_workspace: Workspace):
        result = await git_workspace.git.get_head()

        assert result.head is not None
        assert len(result.head) > 0

    @pytest.mark.asyncio
    async def test_pull_default(self, git_workspace: Workspace):
        # This should not raise an exception
        await git_workspace.git.pull()

    @pytest.mark.asyncio
    async def test_pull_with_remote(self, git_workspace: Workspace):
        await git_workspace.git.pull(remote="origin")

    @pytest.mark.asyncio
    async def test_pull_with_remote_and_branch(self, git_workspace: Workspace):
        await git_workspace.git.pull(remote="origin", branch="master")
