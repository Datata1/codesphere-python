import pytest

from codesphere import CodesphereSDK
from codesphere.core.base import ResourceList
from codesphere.resources.workspace import Workspace
from codesphere.resources.workspace.landscape import (
    Profile,
    ProfileBuilder,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestLandscapeProfilesIntegration:
    """Integration tests for landscape profile listing."""

    async def test_list_profiles_returns_resource_list(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """list_profiles should return a ResourceList."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        profiles = await workspace.landscape.list_profiles()

        assert isinstance(profiles, ResourceList)

    async def test_list_profiles_empty_workspace(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """list_profiles on a fresh workspace should return empty or existing profiles."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        profiles = await workspace.landscape.list_profiles()

        # Fresh workspace may have no profiles, which is valid
        assert isinstance(profiles, ResourceList)
        assert len(profiles) >= 0

    async def test_list_profiles_after_creating_profile_file(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """list_profiles should find a profile after creating a ci.<name>.yml file."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Create a test profile file
        profile_name = "sdk-test-profile"
        create_result = await workspace.execute_command(
            f"echo 'version: 1' > ci.{profile_name}.yml"
        )

        try:
            profiles = await workspace.landscape.list_profiles()

            profile_names = [p.name for p in profiles]
            assert profile_name in profile_names

            # Verify the profile is a Profile instance
            matching_profile = next(p for p in profiles if p.name == profile_name)
            assert isinstance(matching_profile, Profile)

        finally:
            # Cleanup: remove the test profile file
            await workspace.execute_command(f"rm -f ci.{profile_name}.yml")

    async def test_list_profiles_with_multiple_profile_files(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """list_profiles should find multiple profiles."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Create multiple test profile files
        profile_names = ["test-profile-1", "test-profile-2", "test_profile_3"]
        for name in profile_names:
            await workspace.execute_command(f"echo 'version: 1' > ci.{name}.yml")

        try:
            profiles = await workspace.landscape.list_profiles()

            found_names = [p.name for p in profiles]
            for expected_name in profile_names:
                assert expected_name in found_names, (
                    f"Profile {expected_name} not found"
                )

        finally:
            # Cleanup: remove all test profile files
            for name in profile_names:
                await workspace.execute_command(f"rm -f ci.{name}.yml")

    async def test_list_profiles_ignores_non_profile_yml_files(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """list_profiles should not include non-profile yml files."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Create a profile file and a non-profile yml file
        await workspace.execute_command("echo 'version: 1' > ci.valid-profile.yml")
        await workspace.execute_command("echo 'key: value' > config.yml")
        await workspace.execute_command("echo 'services: []' > docker-compose.yml")

        try:
            profiles = await workspace.landscape.list_profiles()

            profile_names = [p.name for p in profiles]
            assert "valid-profile" in profile_names
            # These should NOT be in the list as they don't match ci.<name>.yml pattern
            assert "config" not in profile_names
            assert "docker-compose" not in profile_names

        finally:
            # Cleanup
            await workspace.execute_command(
                "rm -f ci.valid-profile.yml config.yml docker-compose.yml"
            )

    async def test_list_profiles_iterable(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """list_profiles result should be iterable."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Create a test profile
        await workspace.execute_command("echo 'version: 1' > ci.iter-test.yml")

        try:
            profiles = await workspace.landscape.list_profiles()

            # Test iteration
            profile_list = list(profiles)
            assert isinstance(profile_list, list)

            # Test indexing
            if len(profiles) > 0:
                first_profile = profiles[0]
                assert isinstance(first_profile, Profile)

        finally:
            await workspace.execute_command("rm -f ci.iter-test.yml")


class TestLandscapeManagerAccess:
    """Integration tests for accessing the landscape manager."""

    async def test_workspace_has_landscape_property(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Workspace should have a landscape property."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        assert hasattr(workspace, "landscape")
        assert workspace.landscape is not None

    async def test_landscape_manager_is_cached(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Landscape manager should be cached on the workspace instance."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        manager1 = workspace.landscape
        manager2 = workspace.landscape

        assert manager1 is manager2


class TestSaveProfileIntegration:
    """Integration tests for saving landscape profiles."""

    async def test_save_profile_with_builder(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """save_profile should create a profile file using ProfileBuilder."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        profile_name = "sdk-builder-test"

        profile = (
            ProfileBuilder()
            .prepare()
            .add_step("echo 'Installing dependencies'")
            .done()
            .add_reactive_service("web")
            .add_step("echo 'Starting server'")
            .add_port(3000, public=True)
            .replicas(1)
            .done()
            .build()
        )

        try:
            await workspace.landscape.save_profile(profile_name, profile)

            # Verify profile was created
            profiles = await workspace.landscape.list_profiles()
            profile_names = [p.name for p in profiles]
            assert profile_name in profile_names

        finally:
            await workspace.landscape.delete_profile(profile_name)

    async def test_save_profile_with_yaml_string(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """save_profile should accept a raw YAML string."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        profile_name = "sdk-yaml-test"

        yaml_content = """schemaVersion: v0.2
prepare:
  steps:
    - command: echo 'test'
test:
  steps: []
run: {}
"""

        try:
            await workspace.landscape.save_profile(profile_name, yaml_content)

            profiles = await workspace.landscape.list_profiles()
            profile_names = [p.name for p in profiles]
            assert profile_name in profile_names

        finally:
            await workspace.landscape.delete_profile(profile_name)

    async def test_save_profile_overwrites_existing(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """save_profile should overwrite an existing profile."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        profile_name = "sdk-overwrite-test"

        # Create initial profile
        profile_v1 = (
            ProfileBuilder().prepare().add_step("echo 'version 1'").done().build()
        )

        # Create updated profile
        profile_v2 = (
            ProfileBuilder().prepare().add_step("echo 'version 2'").done().build()
        )

        try:
            await workspace.landscape.save_profile(profile_name, profile_v1)
            await workspace.landscape.save_profile(profile_name, profile_v2)

            # Verify content was updated
            content = await workspace.landscape.get_profile(profile_name)
            assert "version 2" in content

        finally:
            await workspace.landscape.delete_profile(profile_name)


class TestGetProfileIntegration:
    """Integration tests for getting landscape profile content."""

    async def test_get_profile_returns_yaml_content(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """get_profile should return the YAML content of a saved profile."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        profile_name = "sdk-get-test"

        profile = (
            ProfileBuilder()
            .prepare()
            .add_step("npm install")
            .done()
            .add_reactive_service("api")
            .add_step("npm start")
            .add_port(8080)
            .env("NODE_ENV", "production")
            .done()
            .build()
        )

        try:
            await workspace.landscape.save_profile(profile_name, profile)

            content = await workspace.landscape.get_profile(profile_name)

            assert "schemaVersion: v0.2" in content
            assert "npm install" in content
            assert "api:" in content
            assert "NODE_ENV" in content

        finally:
            await workspace.landscape.delete_profile(profile_name)


class TestDeleteProfileIntegration:
    """Integration tests for deleting landscape profiles."""

    async def test_delete_profile_removes_file(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """delete_profile should remove the profile file."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        profile_name = "sdk-delete-test"

        profile = ProfileBuilder().build()
        await workspace.landscape.save_profile(profile_name, profile)

        # Verify it exists
        profiles = await workspace.landscape.list_profiles()
        assert profile_name in [p.name for p in profiles]

        # Delete it
        await workspace.landscape.delete_profile(profile_name)

        # Verify it's gone
        profiles = await workspace.landscape.list_profiles()
        assert profile_name not in [p.name for p in profiles]

    async def test_delete_nonexistent_profile_no_error(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """delete_profile should not raise an error for non-existent profiles."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)

        # Should not raise
        await workspace.landscape.delete_profile("nonexistent-profile-xyz")


class TestProfileBuilderIntegration:
    """Integration tests for ProfileBuilder with real workspaces."""

    async def test_complex_profile_roundtrip(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """A complex profile should survive save and retrieve."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        profile_name = "sdk-complex-test"

        profile = (
            ProfileBuilder()
            .prepare()
            .add_step("npm ci", name="Install")
            .add_step("npm run build", name="Build")
            .done()
            .test()
            .add_step("npm test")
            .done()
            .add_reactive_service("frontend")
            .add_step("npm run serve")
            .add_port(3000, public=True)
            .add_path("/", port=3000)
            .replicas(2)
            .env("NODE_ENV", "production")
            .health_endpoint("/health")
            .done()
            .add_reactive_service("backend")
            .add_step("python -m uvicorn main:app")
            .add_port(8000)
            .add_path("/api", port=8000, strip_path=True)
            .envs({"PYTHONPATH": "/app", "LOG_LEVEL": "info"})
            .done()
            .add_managed_service("database", provider="postgres", plan="small")
            .config("max_connections", 50)
            .done()
            .build()
        )

        try:
            await workspace.landscape.save_profile(profile_name, profile)

            content = await workspace.landscape.get_profile(profile_name)

            # Verify key elements are present
            assert "schemaVersion: v0.2" in content
            assert "frontend:" in content
            assert "backend:" in content
            assert "database:" in content
            assert "npm ci" in content
            assert "replicas: 2" in content
            assert "postgres" in content

        finally:
            await workspace.landscape.delete_profile(profile_name)

    async def test_profile_with_special_characters_in_env(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
    ):
        """Profile with special characters in env values should work."""
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        profile_name = "sdk-special-chars-test"

        profile = (
            ProfileBuilder()
            .add_reactive_service("app")
            .add_step("npm start")
            .add_port(3000)
            .env("DATABASE_URL", "postgres://user:p@ss=word@localhost:5432/db")
            .env("API_KEY", "sk-1234567890abcdef")
            .done()
            .build()
        )

        try:
            await workspace.landscape.save_profile(profile_name, profile)

            content = await workspace.landscape.get_profile(profile_name)
            assert "DATABASE_URL" in content
            assert "API_KEY" in content

        finally:
            await workspace.landscape.delete_profile(profile_name)
