import pytest

from codesphere.core.base import ResourceList
from codesphere.resources.workspace.landscape import (
    ManagedServiceBuilder,
    ManagedServiceConfig,
    NetworkConfig,
    PathConfig,
    PortConfig,
    Profile,
    ProfileBuilder,
    ProfileConfig,
    ReactiveServiceBuilder,
    ReactiveServiceConfig,
    StageConfig,
    Step,
    WorkspaceLandscapeManager,
)


class TestWorkspaceLandscapeManager:
    """Tests for the WorkspaceLandscapeManager class."""

    @pytest.fixture
    def landscape_manager(self, mock_http_client_for_resource):
        """Create a WorkspaceLandscapeManager with mock HTTP client."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)
        return manager, mock_client

    @pytest.mark.asyncio
    async def test_deploy_without_profile(self, landscape_manager):
        """Deploy without profile should call the basic deploy endpoint."""
        manager, mock_client = landscape_manager

        await manager.deploy()

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/landscape/deploy"

    @pytest.mark.asyncio
    async def test_deploy_with_profile(self, mock_http_client_for_resource):
        """Deploy with profile should call the profile-specific endpoint."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        await manager.deploy(profile="my-profile")

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert (
            call_args.kwargs.get("endpoint")
            == "/workspaces/72678/landscape/deploy/my-profile"
        )

    @pytest.mark.asyncio
    async def test_teardown(self, landscape_manager):
        """Teardown should call the teardown endpoint."""
        manager, mock_client = landscape_manager

        await manager.teardown()

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "DELETE"
        assert (
            call_args.kwargs.get("endpoint") == "/workspaces/72678/landscape/teardown"
        )

    @pytest.mark.asyncio
    async def test_scale_services(self, mock_http_client_for_resource):
        """Scale should call the scale endpoint with service configuration."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        services = {"web": 3, "worker": 2}
        await manager.scale(services=services)

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "PATCH"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/landscape/scale"
        assert call_args.kwargs.get("json") == {"web": 3, "worker": 2}

    @pytest.mark.asyncio
    async def test_scale_single_service(self, mock_http_client_for_resource):
        """Scale should work with a single service."""
        mock_client = mock_http_client_for_resource(None)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        services = {"api": 5}
        await manager.scale(services=services)

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("json") == {"api": 5}


class TestListProfiles:
    """Tests for the list_profiles method."""

    @pytest.fixture
    def mock_command_response(self):
        """Factory to create mock command output responses."""

        def _create(output: str, error: str = ""):
            return {
                "command": "ls -1 *.yml 2>/dev/null || true",
                "workingDir": "/home/user",
                "output": output,
                "error": error,
            }

        return _create

    @pytest.mark.asyncio
    async def test_list_profiles_with_multiple_profiles(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """list_profiles should return profiles from ci.<name>.yml files."""
        response_data = mock_command_response(
            "ci.production.yml\nci.staging.yml\nci.dev-test.yml\n"
        )
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        result = await manager.list_profiles()

        assert isinstance(result, ResourceList)
        assert len(result) == 3
        assert result[0].name == "production"
        assert result[1].name == "staging"
        assert result[2].name == "dev-test"

    @pytest.mark.asyncio
    async def test_list_profiles_with_single_profile(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """list_profiles should work with a single profile."""
        response_data = mock_command_response("ci.main.yml\n")
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        result = await manager.list_profiles()

        assert len(result) == 1
        assert result[0].name == "main"

    @pytest.mark.asyncio
    async def test_list_profiles_with_no_profiles(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """list_profiles should return empty list when no profiles exist."""
        response_data = mock_command_response("")
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        result = await manager.list_profiles()

        assert isinstance(result, ResourceList)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_profiles_filters_non_profile_yml_files(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """list_profiles should filter out non-profile yml files."""
        response_data = mock_command_response(
            "ci.production.yml\nconfig.yml\ndocker-compose.yml\nci.staging.yml\n"
        )
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        result = await manager.list_profiles()

        assert len(result) == 2
        profile_names = [p.name for p in result]
        assert "production" in profile_names
        assert "staging" in profile_names

    @pytest.mark.asyncio
    async def test_list_profiles_with_underscore_in_name(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """list_profiles should handle underscores in profile names."""
        response_data = mock_command_response("ci.my_profile.yml\n")
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        result = await manager.list_profiles()

        assert len(result) == 1
        assert result[0].name == "my_profile"

    @pytest.mark.asyncio
    async def test_list_profiles_calls_execute_endpoint(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """list_profiles should call the execute command endpoint."""
        response_data = mock_command_response("")
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        await manager.list_profiles()

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/execute"


class TestProfileModel:
    """Tests for the Profile model."""

    def test_create_profile(self):
        """Profile should be created with a name."""
        profile = Profile(name="production")

        assert profile.name == "production"

    def test_profile_from_dict(self):
        """Profile should be created from dictionary."""
        profile = Profile.model_validate({"name": "staging"})

        assert profile.name == "staging"

    def test_profile_dump(self):
        """Profile should dump to dictionary correctly."""
        profile = Profile(name="dev")
        dumped = profile.model_dump()

        assert dumped == {"name": "dev"}


class TestWorkspaceLandscapeManagerAccess:
    """Tests for accessing the landscape manager from a Workspace instance."""

    @pytest.mark.asyncio
    async def test_workspace_landscape_property(self, workspace_model_factory):
        """Workspace should expose a landscape property."""
        workspace, _ = workspace_model_factory()

        landscape_manager = workspace.landscape

        assert isinstance(landscape_manager, WorkspaceLandscapeManager)

    @pytest.mark.asyncio
    async def test_workspace_landscape_is_cached(self, workspace_model_factory):
        """Landscape manager should be cached on the workspace."""
        workspace, _ = workspace_model_factory()

        manager1 = workspace.landscape
        manager2 = workspace.landscape

        assert manager1 is manager2


class TestSaveProfile:
    """Tests for the save_profile method."""

    @pytest.fixture
    def mock_command_response(self):
        """Factory to create mock command output responses."""

        def _create(output: str = "", error: str = ""):
            return {
                "command": "",
                "workingDir": "/home/user",
                "output": output,
                "error": error,
            }

        return _create

    @pytest.mark.asyncio
    async def test_save_profile_with_profile_config(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """save_profile should write a ProfileConfig to a file."""
        response_data = mock_command_response()
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        config = ProfileConfig()
        await manager.save_profile("production", config)

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/execute"

    @pytest.mark.asyncio
    async def test_save_profile_with_yaml_string(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """save_profile should accept a raw YAML string."""
        response_data = mock_command_response()
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        yaml_content = "schemaVersion: v0.2\nprepare:\n  steps: []\n"
        await manager.save_profile("staging", yaml_content)

        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_save_profile_invalid_name_raises_error(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """save_profile should raise ValueError for invalid profile names."""
        response_data = mock_command_response()
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        with pytest.raises(ValueError, match="Invalid profile name"):
            await manager.save_profile("invalid/name", ProfileConfig())

    @pytest.mark.asyncio
    async def test_save_profile_invalid_name_with_spaces(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """save_profile should reject names with spaces."""
        response_data = mock_command_response()
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        with pytest.raises(ValueError):
            await manager.save_profile("my profile", ProfileConfig())


class TestGetProfile:
    """Tests for the get_profile method."""

    @pytest.fixture
    def mock_command_response(self):
        """Factory to create mock command output responses."""

        def _create(output: str = "", error: str = ""):
            return {
                "command": "",
                "workingDir": "/home/user",
                "output": output,
                "error": error,
            }

        return _create

    @pytest.mark.asyncio
    async def test_get_profile_returns_yaml_content(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """get_profile should return the YAML content of a profile."""
        yaml_content = "schemaVersion: v0.2\nprepare:\n  steps: []\n"
        response_data = mock_command_response(output=yaml_content)
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        result = await manager.get_profile("production")

        assert result == yaml_content

    @pytest.mark.asyncio
    async def test_get_profile_invalid_name_raises_error(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """get_profile should raise ValueError for invalid profile names."""
        response_data = mock_command_response()
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        with pytest.raises(ValueError, match="Invalid profile name"):
            await manager.get_profile("invalid/name")


class TestDeleteProfile:
    """Tests for the delete_profile method."""

    @pytest.fixture
    def mock_command_response(self):
        """Factory to create mock command output responses."""

        def _create(output: str = "", error: str = ""):
            return {
                "command": "",
                "workingDir": "/home/user",
                "output": output,
                "error": error,
            }

        return _create

    @pytest.mark.asyncio
    async def test_delete_profile_calls_rm_command(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """delete_profile should execute rm command."""
        response_data = mock_command_response()
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        await manager.delete_profile("production")

        mock_client.request.assert_awaited_once()
        call_args = mock_client.request.call_args
        assert call_args.kwargs.get("method") == "POST"
        assert call_args.kwargs.get("endpoint") == "/workspaces/72678/execute"

    @pytest.mark.asyncio
    async def test_delete_profile_invalid_name_raises_error(
        self, mock_http_client_for_resource, mock_command_response
    ):
        """delete_profile should raise ValueError for invalid profile names."""
        response_data = mock_command_response()
        mock_client = mock_http_client_for_resource(response_data)
        manager = WorkspaceLandscapeManager(http_client=mock_client, workspace_id=72678)

        with pytest.raises(ValueError, match="Invalid profile name"):
            await manager.delete_profile("../etc/passwd")


class TestProfileBuilder:
    """Tests for the ProfileBuilder fluent API."""

    def test_build_empty_profile(self):
        """ProfileBuilder should create an empty profile."""
        profile = ProfileBuilder().build()

        assert isinstance(profile, ProfileConfig)
        assert profile.schema_version == "v0.2"
        assert len(profile.prepare.steps) == 0
        assert len(profile.test.steps) == 0
        assert len(profile.run) == 0

    def test_build_with_prepare_steps(self):
        """ProfileBuilder should add prepare stage steps."""
        profile = (
            ProfileBuilder()
            .prepare()
            .add_step("npm install")
            .add_step("npm run build", name="Build")
            .done()
            .build()
        )

        assert len(profile.prepare.steps) == 2
        assert profile.prepare.steps[0].command == "npm install"
        assert profile.prepare.steps[0].name is None
        assert profile.prepare.steps[1].command == "npm run build"
        assert profile.prepare.steps[1].name == "Build"

    def test_build_with_test_steps(self):
        """ProfileBuilder should add test stage steps."""
        profile = ProfileBuilder().test().add_step("npm test").done().build()

        assert len(profile.test.steps) == 1
        assert profile.test.steps[0].command == "npm test"

    def test_build_with_reactive_service(self):
        """ProfileBuilder should add reactive services."""
        profile = (
            ProfileBuilder()
            .add_reactive_service("web")
            .add_step("npm start")
            .add_port(3000, public=True)
            .replicas(2)
            .env("NODE_ENV", "production")
            .done()
            .build()
        )

        assert "web" in profile.run
        service = profile.run["web"]
        assert isinstance(service, ReactiveServiceConfig)
        assert len(service.steps) == 1
        assert service.replicas == 2
        assert service.env == {"NODE_ENV": "production"}
        assert service.network is not None
        assert len(service.network.ports) == 1
        assert service.network.ports[0].port == 3000
        assert service.network.ports[0].is_public is True

    def test_build_with_reactive_service_paths(self):
        """ProfileBuilder should add path routing to reactive services."""
        profile = (
            ProfileBuilder()
            .add_reactive_service("api")
            .add_port(8080)
            .add_path("/api", port=8080, strip_path=True)
            .add_path("/health", port=8080)
            .done()
            .build()
        )

        service = profile.run["api"]
        assert isinstance(service, ReactiveServiceConfig)
        assert len(service.network.paths) == 2
        assert service.network.paths[0].path == "/api"
        assert service.network.paths[0].strip_path is True
        assert service.network.paths[1].path == "/health"

    def test_build_with_reactive_service_all_options(self):
        """ProfileBuilder should support all reactive service options."""
        profile = (
            ProfileBuilder()
            .add_reactive_service("worker")
            .add_step("python worker.py")
            .plan(123)
            .replicas(3)
            .base_image("python:3.11")
            .run_as(user=1000, group=1000)
            .mount_sub_path("/data")
            .health_endpoint("/health")
            .envs({"KEY1": "value1", "KEY2": "value2"})
            .done()
            .build()
        )

        service = profile.run["worker"]
        assert isinstance(service, ReactiveServiceConfig)
        assert service.plan == 123
        assert service.replicas == 3
        assert service.base_image == "python:3.11"
        assert service.run_as_user == 1000
        assert service.run_as_group == 1000
        assert service.mount_sub_path == "/data"
        assert service.health_endpoint == "/health"
        assert service.env == {"KEY1": "value1", "KEY2": "value2"}

    def test_build_with_managed_service(self):
        """ProfileBuilder should add managed services."""
        profile = (
            ProfileBuilder()
            .add_managed_service("db", provider="postgres", plan="small")
            .config("max_connections", 100)
            .secret("password", "vault://secrets/db-password")
            .done()
            .build()
        )

        assert "db" in profile.run
        service = profile.run["db"]
        assert isinstance(service, ManagedServiceConfig)
        assert service.provider == "postgres"
        assert service.plan == "small"
        assert service.config == {"max_connections": 100}
        assert service.secrets == {"password": "vault://secrets/db-password"}

    def test_build_with_multiple_services(self):
        """ProfileBuilder should support multiple services."""
        profile = (
            ProfileBuilder()
            .prepare()
            .add_step("npm install")
            .done()
            .add_reactive_service("web")
            .add_step("npm start")
            .add_port(3000)
            .done()
            .add_reactive_service("worker")
            .add_step("npm run worker")
            .done()
            .add_managed_service("redis", provider="redis", plan="micro")
            .done()
            .build()
        )

        assert len(profile.prepare.steps) == 1
        assert len(profile.run) == 3
        assert "web" in profile.run
        assert "worker" in profile.run
        assert "redis" in profile.run

    def test_profile_to_yaml(self):
        """ProfileConfig should serialize to YAML correctly."""
        profile = (
            ProfileBuilder()
            .prepare()
            .add_step("npm install")
            .done()
            .add_reactive_service("web")
            .add_step("npm start")
            .add_port(3000, public=True)
            .done()
            .build()
        )

        yaml_output = profile.to_yaml()

        assert "schemaVersion: v0.2" in yaml_output
        assert "prepare:" in yaml_output
        assert "npm install" in yaml_output
        assert "run:" in yaml_output
        assert "web:" in yaml_output


class TestReactiveServiceBuilder:
    """Tests for the standalone ReactiveServiceBuilder."""

    def test_build_reactive_service(self):
        """ReactiveServiceBuilder should create a service configuration."""
        name, config = (
            ReactiveServiceBuilder("api")
            .add_step("npm start")
            .add_port(8080, public=True)
            .replicas(2)
            .build()
        )

        assert name == "api"
        assert isinstance(config, ReactiveServiceConfig)
        assert config.replicas == 2

    def test_service_name_property(self):
        """ReactiveServiceBuilder should expose the service name."""
        builder = ReactiveServiceBuilder("my-service")
        assert builder.name == "my-service"


class TestManagedServiceBuilder:
    """Tests for the standalone ManagedServiceBuilder."""

    def test_build_managed_service(self):
        """ManagedServiceBuilder should create a managed service configuration."""
        name, config = (
            ManagedServiceBuilder("cache", "redis", "medium")
            .config("maxmemory", "256mb")
            .secrets({"auth_token": "secret"})
            .build()
        )

        assert name == "cache"
        assert isinstance(config, ManagedServiceConfig)
        assert config.provider == "redis"
        assert config.plan == "medium"
        assert config.config == {"maxmemory": "256mb"}
        assert config.secrets == {"auth_token": "secret"}


class TestProfileConfigModels:
    """Tests for the profile configuration Pydantic models."""

    def test_step_model(self):
        """Step model should have command and optional name."""
        step = Step(command="echo hello")
        assert step.command == "echo hello"
        assert step.name is None

        step_with_name = Step(command="npm build", name="Build")
        assert step_with_name.name == "Build"

    def test_port_config_validation(self):
        """PortConfig should validate port range."""
        port = PortConfig(port=8080, is_public=False)
        assert port.port == 8080

        with pytest.raises(ValueError):
            PortConfig(port=0)

        with pytest.raises(ValueError):
            PortConfig(port=70000)

    def test_path_config_model(self):
        """PathConfig model should have port, path, and optional strip_path."""
        path = PathConfig(port=3000, path="/api")
        assert path.port == 3000
        assert path.path == "/api"
        assert path.strip_path is None

    def test_network_config_model(self):
        """NetworkConfig should contain ports and paths."""
        network = NetworkConfig(
            ports=[PortConfig(port=3000, is_public=True)],
            paths=[PathConfig(port=3000, path="/")],
        )
        assert len(network.ports) == 1
        assert len(network.paths) == 1

    def test_reactive_service_config_defaults(self):
        """ReactiveServiceConfig should have sensible defaults."""
        config = ReactiveServiceConfig()
        assert config.replicas == 1
        assert config.steps == []
        assert config.env is None
        assert config.network is None

    def test_managed_service_config(self):
        """ManagedServiceConfig should have provider and plan."""
        config = ManagedServiceConfig(provider="postgres", plan="large")
        assert config.provider == "postgres"
        assert config.plan == "large"

    def test_stage_config_defaults(self):
        """StageConfig should have empty steps by default."""
        stage = StageConfig()
        assert stage.steps == []

    def test_profile_config_camel_case_serialization(self):
        """ProfileConfig should serialize with camelCase keys."""
        profile = ProfileConfig()
        data = profile.model_dump(by_alias=True)

        assert "schemaVersion" in data
        assert "schema_version" not in data
