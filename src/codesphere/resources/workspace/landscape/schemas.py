from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field

from ....core.base import CamelModel


class Profile(BaseModel):
    """Landscape deployment profile model."""

    name: str


class Step(CamelModel):
    """A step in a pipeline stage."""

    name: Optional[str] = None
    command: str


class PortConfig(CamelModel):
    """Port configuration for a reactive service."""

    port: int = Field(ge=1, le=65535)
    is_public: bool = False


class PathConfig(CamelModel):
    """Path routing configuration for a reactive service."""

    port: int = Field(ge=1, le=65535)
    path: str
    strip_path: Optional[bool] = None


class NetworkConfig(CamelModel):
    """Network configuration for a reactive service."""

    ports: List[PortConfig] = Field(default_factory=list)
    paths: List[PathConfig] = Field(default_factory=list)


class ReactiveServiceConfig(CamelModel):
    """Configuration for a reactive (custom) service in the run stage."""

    steps: List[Step] = Field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    plan: Optional[int] = None
    replicas: int = 1
    base_image: Optional[str] = None
    run_as_user: Optional[int] = Field(default=None, ge=0, le=65534)
    run_as_group: Optional[int] = Field(default=None, ge=0, le=65534)
    mount_sub_path: Optional[str] = None
    health_endpoint: Optional[str] = None
    network: Optional[NetworkConfig] = None


class ManagedServiceConfig(CamelModel):
    """Configuration for a managed service (e.g., database) in the run stage."""

    provider: str
    plan: str
    config: Optional[Dict[str, Any]] = None
    secrets: Optional[Dict[str, str]] = None


class StageConfig(CamelModel):
    """Configuration for a pipeline stage (prepare/test)."""

    steps: List[Step] = Field(default_factory=list)


class ProfileConfig(CamelModel):
    """Complete pipeline configuration for a landscape profile (schema v0.2)."""

    schema_version: Literal["v0.2"] = Field(default="v0.2", alias="schemaVersion")
    prepare: StageConfig = Field(default_factory=StageConfig)
    test: StageConfig = Field(default_factory=StageConfig)
    run: Dict[str, ReactiveServiceConfig | ManagedServiceConfig] = Field(
        default_factory=dict
    )

    def to_yaml(self, *, exclude_none: bool = True) -> str:
        """Export the profile configuration as YAML.

        Args:
            exclude_none: Exclude fields with None values if True.

        Returns:
            YAML string representation of the profile.
        """
        data = self.model_dump(by_alias=True, exclude_none=exclude_none, mode="json")
        return yaml.safe_dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


# =============================================================================
# Fluent Builder Classes
# =============================================================================


class StepBuilder:
    """Fluent builder for pipeline steps."""

    def __init__(self, command: str, name: Optional[str] = None):
        self._command = command
        self._name = name

    def build(self) -> Step:
        """Build the Step instance."""
        return Step(command=self._command, name=self._name)


class PortBuilder:
    """Fluent builder for port configuration."""

    def __init__(self, port: int):
        self._port = port
        self._is_public = False

    def public(self, is_public: bool = True) -> PortBuilder:
        """Set whether the port is publicly accessible."""
        self._is_public = is_public
        return self

    def build(self) -> PortConfig:
        """Build the PortConfig instance."""
        return PortConfig(port=self._port, is_public=self._is_public)


class PathBuilder:
    """Fluent builder for path routing configuration."""

    def __init__(self, path: str, port: int):
        self._path = path
        self._port = port
        self._strip_path: Optional[bool] = None

    def strip_path(self, strip: bool = True) -> PathBuilder:
        """Set whether to strip the path prefix when forwarding."""
        self._strip_path = strip
        return self

    def build(self) -> PathConfig:
        """Build the PathConfig instance."""
        return PathConfig(port=self._port, path=self._path, strip_path=self._strip_path)


class ReactiveServiceBuilder:
    """Fluent builder for reactive (custom) service configuration."""

    def __init__(self, name: str):
        self._name = name
        self._steps: List[Step] = []
        self._env: Dict[str, str] = {}
        self._plan: Optional[int] = None
        self._replicas: int = 1
        self._base_image: Optional[str] = None
        self._run_as_user: Optional[int] = None
        self._run_as_group: Optional[int] = None
        self._mount_sub_path: Optional[str] = None
        self._health_endpoint: Optional[str] = None
        self._ports: List[PortConfig] = []
        self._paths: List[PathConfig] = []

    @property
    def name(self) -> str:
        """Get the service name."""
        return self._name

    def add_step(
        self, command: str, name: Optional[str] = None
    ) -> ReactiveServiceBuilder:
        """Add a step to the service.

        Args:
            command: The command to execute.
            name: Optional name for the step.
        """
        self._steps.append(Step(command=command, name=name))
        return self

    def env(self, key: str, value: str) -> ReactiveServiceBuilder:
        """Add an environment variable.

        Args:
            key: Environment variable name.
            value: Environment variable value.
        """
        self._env[key] = value
        return self

    def envs(self, env_vars: Dict[str, str]) -> ReactiveServiceBuilder:
        """Add multiple environment variables.

        Args:
            env_vars: Dictionary of environment variables.
        """
        self._env.update(env_vars)
        return self

    def plan(self, plan_id: int) -> ReactiveServiceBuilder:
        """Set the plan ID for the service.

        Args:
            plan_id: The workspace plan ID.
        """
        self._plan = plan_id
        return self

    def replicas(self, count: int) -> ReactiveServiceBuilder:
        """Set the number of replicas.

        Args:
            count: Number of replicas (minimum 1).
        """
        self._replicas = max(1, count)
        return self

    def base_image(self, image: str) -> ReactiveServiceBuilder:
        """Set the base image for the service.

        Args:
            image: Docker image reference.
        """
        self._base_image = image
        return self

    def run_as(
        self, user: Optional[int] = None, group: Optional[int] = None
    ) -> ReactiveServiceBuilder:
        """Set the user and group to run the service as.

        Args:
            user: User ID (0-65534).
            group: Group ID (0-65534).
        """
        self._run_as_user = user
        self._run_as_group = group
        return self

    def mount_sub_path(self, path: str) -> ReactiveServiceBuilder:
        """Set the mount sub-path.

        Args:
            path: Sub-path to mount.
        """
        self._mount_sub_path = path
        return self

    def health_endpoint(self, endpoint: str) -> ReactiveServiceBuilder:
        """Set the health check endpoint.

        Args:
            endpoint: Health check endpoint path.
        """
        self._health_endpoint = endpoint
        return self

    def add_port(self, port: int, *, public: bool = False) -> ReactiveServiceBuilder:
        """Add a port to the service.

        Args:
            port: Port number (1-65535).
            public: Whether the port is publicly accessible.
        """
        self._ports.append(PortConfig(port=port, is_public=public))
        return self

    def add_path(
        self, path: str, port: int, *, strip_path: Optional[bool] = None
    ) -> ReactiveServiceBuilder:
        """Add a path routing rule.

        Args:
            path: URL path to route.
            port: Port to forward to.
            strip_path: Whether to strip the path prefix.
        """
        self._paths.append(PathConfig(port=port, path=path, strip_path=strip_path))
        return self

    def build(self) -> tuple[str, ReactiveServiceConfig]:
        """Build the service configuration.

        Returns:
            Tuple of (service_name, ReactiveServiceConfig).
        """
        network = None
        if self._ports or self._paths:
            network = NetworkConfig(ports=self._ports, paths=self._paths)

        config = ReactiveServiceConfig(
            steps=self._steps,
            env=self._env if self._env else None,
            plan=self._plan,
            replicas=self._replicas,
            base_image=self._base_image,
            run_as_user=self._run_as_user,
            run_as_group=self._run_as_group,
            mount_sub_path=self._mount_sub_path,
            health_endpoint=self._health_endpoint,
            network=network,
        )
        return self._name, config


class ManagedServiceBuilder:
    """Fluent builder for managed service configuration."""

    def __init__(self, name: str, provider: str, plan: str):
        self._name = name
        self._provider = provider
        self._plan = plan
        self._config: Dict[str, Any] = {}
        self._secrets: Dict[str, str] = {}

    @property
    def name(self) -> str:
        """Get the service name."""
        return self._name

    def config(self, key: str, value: Any) -> ManagedServiceBuilder:
        """Add a configuration option.

        Args:
            key: Configuration key.
            value: Configuration value.
        """
        self._config[key] = value
        return self

    def configs(self, config: Dict[str, Any]) -> ManagedServiceBuilder:
        """Add multiple configuration options.

        Args:
            config: Dictionary of configuration options.
        """
        self._config.update(config)
        return self

    def secret(self, key: str, value: str) -> ManagedServiceBuilder:
        """Add a secret.

        Args:
            key: Secret key.
            value: Secret value (or vault reference).
        """
        self._secrets[key] = value
        return self

    def secrets(self, secrets: Dict[str, str]) -> ManagedServiceBuilder:
        """Add multiple secrets.

        Args:
            secrets: Dictionary of secrets.
        """
        self._secrets.update(secrets)
        return self

    def build(self) -> tuple[str, ManagedServiceConfig]:
        """Build the managed service configuration.

        Returns:
            Tuple of (service_name, ManagedServiceConfig).
        """
        config = ManagedServiceConfig(
            provider=self._provider,
            plan=self._plan,
            config=self._config if self._config else None,
            secrets=self._secrets if self._secrets else None,
        )
        return self._name, config


class ProfileBuilder:
    """Fluent builder for creating landscape profile configurations.

    Example:
        ```python
        profile = (
            ProfileBuilder()
            .prepare()
                .add_step("npm install")
                .add_step("npm run build")
            .done()
            .add_reactive_service("web")
                .add_step("npm start")
                .add_port(3000, public=True)
                .add_path("/api", port=3000)
                .replicas(2)
                .env("NODE_ENV", "production")
            .done()
            .add_managed_service("db", provider="postgres", plan="small")
                .config("max_connections", 100)
            .done()
            .build()
        )

        # Save to workspace
        await workspace.landscape.save_profile("production", profile)
        ```
    """

    def __init__(self) -> None:
        self._prepare_steps: List[Step] = []
        self._test_steps: List[Step] = []
        self._services: Dict[str, ReactiveServiceConfig | ManagedServiceConfig] = {}

    def prepare(self) -> PrepareStageBuilder:
        """Configure the prepare stage.

        Returns:
            A PrepareStageBuilder for fluent configuration.
        """
        return PrepareStageBuilder(self)

    def test(self) -> TestStageBuilder:
        """Configure the test stage.

        Returns:
            A TestStageBuilder for fluent configuration.
        """
        return TestStageBuilder(self)

    def add_reactive_service(self, name: str) -> ReactiveServiceBuilderContext:
        """Add a reactive (custom) service to the run stage.

        Args:
            name: Unique name for the service.

        Returns:
            A ReactiveServiceBuilderContext for fluent configuration.
        """
        return ReactiveServiceBuilderContext(self, name)

    def add_managed_service(
        self, name: str, *, provider: str, plan: str
    ) -> ManagedServiceBuilderContext:
        """Add a managed service (e.g., database) to the run stage.

        Args:
            name: Unique name for the service.
            provider: Service provider (e.g., "postgres", "redis").
            plan: Service plan (e.g., "small", "medium").

        Returns:
            A ManagedServiceBuilderContext for fluent configuration.
        """
        return ManagedServiceBuilderContext(self, name, provider, plan)

    def build(self) -> ProfileConfig:
        """Build the complete profile configuration.

        Returns:
            A ProfileConfig instance ready to be saved.
        """
        return ProfileConfig(
            prepare=StageConfig(steps=self._prepare_steps),
            test=StageConfig(steps=self._test_steps),
            run=self._services,
        )


class PrepareStageBuilder:
    """Builder context for the prepare stage."""

    def __init__(self, parent: ProfileBuilder):
        self._parent = parent

    def add_step(self, command: str, name: Optional[str] = None) -> PrepareStageBuilder:
        """Add a step to the prepare stage.

        Args:
            command: The command to execute.
            name: Optional name for the step.
        """
        self._parent._prepare_steps.append(Step(command=command, name=name))
        return self

    def done(self) -> ProfileBuilder:
        """Return to the parent ProfileBuilder."""
        return self._parent


class TestStageBuilder:
    """Builder context for the test stage."""

    def __init__(self, parent: ProfileBuilder):
        self._parent = parent

    def add_step(self, command: str, name: Optional[str] = None) -> TestStageBuilder:
        """Add a step to the test stage.

        Args:
            command: The command to execute.
            name: Optional name for the step.
        """
        self._parent._test_steps.append(Step(command=command, name=name))
        return self

    def done(self) -> ProfileBuilder:
        """Return to the parent ProfileBuilder."""
        return self._parent


class ReactiveServiceBuilderContext:
    """Builder context for a reactive service within a ProfileBuilder."""

    def __init__(self, parent: ProfileBuilder, name: str):
        self._parent = parent
        self._builder = ReactiveServiceBuilder(name)

    def add_step(
        self, command: str, name: Optional[str] = None
    ) -> ReactiveServiceBuilderContext:
        """Add a step to the service."""
        self._builder.add_step(command, name)
        return self

    def env(self, key: str, value: str) -> ReactiveServiceBuilderContext:
        """Add an environment variable."""
        self._builder.env(key, value)
        return self

    def envs(self, env_vars: Dict[str, str]) -> ReactiveServiceBuilderContext:
        """Add multiple environment variables."""
        self._builder.envs(env_vars)
        return self

    def plan(self, plan_id: int) -> ReactiveServiceBuilderContext:
        """Set the plan ID."""
        self._builder.plan(plan_id)
        return self

    def replicas(self, count: int) -> ReactiveServiceBuilderContext:
        """Set the number of replicas."""
        self._builder.replicas(count)
        return self

    def base_image(self, image: str) -> ReactiveServiceBuilderContext:
        """Set the base image."""
        self._builder.base_image(image)
        return self

    def run_as(
        self, user: Optional[int] = None, group: Optional[int] = None
    ) -> ReactiveServiceBuilderContext:
        """Set user and group IDs."""
        self._builder.run_as(user, group)
        return self

    def mount_sub_path(self, path: str) -> ReactiveServiceBuilderContext:
        """Set the mount sub-path."""
        self._builder.mount_sub_path(path)
        return self

    def health_endpoint(self, endpoint: str) -> ReactiveServiceBuilderContext:
        """Set the health check endpoint."""
        self._builder.health_endpoint(endpoint)
        return self

    def add_port(
        self, port: int, *, public: bool = False
    ) -> ReactiveServiceBuilderContext:
        """Add a port to the service."""
        self._builder.add_port(port, public=public)
        return self

    def add_path(
        self, path: str, port: int, *, strip_path: Optional[bool] = None
    ) -> ReactiveServiceBuilderContext:
        """Add a path routing rule."""
        self._builder.add_path(path, port, strip_path=strip_path)
        return self

    def done(self) -> ProfileBuilder:
        """Finalize the service and return to the parent ProfileBuilder."""
        name, config = self._builder.build()
        self._parent._services[name] = config
        return self._parent


class ManagedServiceBuilderContext:
    """Builder context for a managed service within a ProfileBuilder."""

    def __init__(self, parent: ProfileBuilder, name: str, provider: str, plan: str):
        self._parent = parent
        self._builder = ManagedServiceBuilder(name, provider, plan)

    def config(self, key: str, value: Any) -> ManagedServiceBuilderContext:
        """Add a configuration option."""
        self._builder.config(key, value)
        return self

    def configs(self, config: Dict[str, Any]) -> ManagedServiceBuilderContext:
        """Add multiple configuration options."""
        self._builder.configs(config)
        return self

    def secret(self, key: str, value: str) -> ManagedServiceBuilderContext:
        """Add a secret."""
        self._builder.secret(key, value)
        return self

    def secrets(self, secrets: Dict[str, str]) -> ManagedServiceBuilderContext:
        """Add multiple secrets."""
        self._builder.secrets(secrets)
        return self

    def done(self) -> ProfileBuilder:
        """Finalize the service and return to the parent ProfileBuilder."""
        name, config = self._builder.build()
        self._parent._services[name] = config
        return self._parent
