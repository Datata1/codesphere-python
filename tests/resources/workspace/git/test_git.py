import pytest

from codesphere.resources.workspace.git import GitHead, WorkspaceGitManager


class TestWorkspaceGitManager:
    @pytest.fixture
    def git_manager(self, mock_http_client_for_resource):
        def _create(response_data):
            mock_client = mock_http_client_for_resource(response_data)
            manager = WorkspaceGitManager(http_client=mock_client, workspace_id=72678)
            return manager, mock_client

        return _create

    @pytest.mark.asyncio
    async def test_get_head(self, git_manager):
        manager, mock_client = git_manager({"head": "abc123def456"})

        result = await manager.get_head()

        assert isinstance(result, GitHead)
        assert result.head == "abc123def456"
        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "GET"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/git/head"

    @pytest.mark.asyncio
    async def test_pull_without_arguments(self, git_manager):
        manager, mock_client = git_manager(None)

        await manager.pull()

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/git/pull"

    @pytest.mark.asyncio
    async def test_pull_with_remote(self, git_manager):
        manager, mock_client = git_manager(None)

        await manager.pull(remote="origin")

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/git/pull/origin"

    @pytest.mark.asyncio
    async def test_pull_with_remote_and_branch(self, git_manager):
        manager, mock_client = git_manager(None)

        await manager.pull(remote="origin", branch="main")

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert (
            call_args.kwargs.get("endpoint") == "/workspaces/72678/git/pull/origin/main"
        )

    @pytest.mark.asyncio
    async def test_pull_with_branch_only_ignores_branch(self, git_manager):
        manager, mock_client = git_manager(None)

        # Branch without remote should be ignored per the implementation
        await manager.pull(branch="main")

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/git/pull"

    @pytest.mark.asyncio
    async def test_pull_with_custom_remote(self, git_manager):
        """pull should work with custom remote names."""
        manager, mock_client = git_manager(None)

        await manager.pull(remote="upstream")

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/git/pull/upstream"

    @pytest.mark.asyncio
    async def test_pull_with_feature_branch(self, git_manager):
        manager, mock_client = git_manager(None)

        await manager.pull(remote="origin", branch="feature/my-feature")

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert (
            call_args.kwargs.get("endpoint")
            == "/workspaces/72678/git/pull/origin/feature/my-feature"
        )


class TestGitHeadModel:
    def test_create_git_head(self):
        git_head = GitHead(head="abc123def456")

        assert git_head.head == "abc123def456"

    def test_git_head_from_dict(self):
        git_head = GitHead.model_validate({"head": "abc123def456"})

        assert git_head.head == "abc123def456"

    def test_git_head_dump(self):
        git_head = GitHead(head="abc123def456")
        dumped = git_head.model_dump()

        assert dumped == {"head": "abc123def456"}

    def test_git_head_with_full_sha(self):
        full_sha = "a" * 40
        git_head = GitHead(head=full_sha)

        assert git_head.head == full_sha
        assert len(git_head.head) == 40
