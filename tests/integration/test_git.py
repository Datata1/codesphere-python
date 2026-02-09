import pytest

from codesphere.resources.workspace import Workspace

pytestmark = pytest.mark.integration


class TestGitIntegration:
    @pytest.mark.asyncio
    async def test_get_head(self, workspace_with_git: Workspace):
        result = await workspace_with_git.git.get_head()

        assert result.head is not None
        assert len(result.head) > 0

    @pytest.mark.asyncio
    async def test_pull_default(self, workspace_with_git: Workspace):
        await workspace_with_git.git.pull()

    @pytest.mark.asyncio
    async def test_pull_with_remote(self, workspace_with_git: Workspace):
        await workspace_with_git.git.pull(remote="origin")

    @pytest.mark.asyncio
    async def test_pull_with_remote_and_branch(self, workspace_with_git: Workspace):
        await workspace_with_git.git.pull(remote="origin", branch="master")
