from __future__ import annotations

from enum import Enum
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from ..core.models import CamelModel, ResourceList


class PipelineStage(str, Enum):
    PREPARE = "prepare"
    TEST = "test"
    RUN = "run"


class PipelineState(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    ABORTED = "aborted"


class StepStatus(CamelModel):
    state: PipelineState
    started_at: str | None = None
    finished_at: str | None = None


class PipelineStatus(CamelModel):
    state: PipelineState
    started_at: str | None = None
    finished_at: str | None = None
    steps: list[StepStatus] = Field(default_factory=list)
    replica: str
    server: str


# Alias kept for backwards compatibility; ResourceList provides the same API.
PipelineStatusList = ResourceList[PipelineStatus]


class Profile(BaseModel):
    name: str


class Step(CamelModel):
    name: str | None = None
    command: str


class PortConfig(CamelModel):
    port: int = Field(ge=1, le=65535)
    is_public: bool = False


class PathConfig(CamelModel):
    port: int = Field(ge=1, le=65535)
    path: str
    strip_path: bool | None = None


class NetworkConfig(CamelModel):
    ports: list[PortConfig] = Field(default_factory=list)
    paths: list[PathConfig] = Field(default_factory=list)


class ReactiveServiceConfig(CamelModel):
    steps: list[Step] = Field(default_factory=list)
    plan: int
    replicas: int = 1
    env: dict[str, str] | None = None
    base_image: str | None = None
    run_as_user: int | None = Field(default=None, ge=0, le=65534)
    run_as_group: int | None = Field(default=None, ge=0, le=65534)
    mount_sub_path: str | None = None
    health_endpoint: str | None = None
    network: NetworkConfig | None = None


class ManagedServiceConfig(CamelModel):
    provider: str
    plan: str
    config: dict[str, Any] | None = None
    secrets: dict[str, str] | None = None


class StageConfig(CamelModel):
    steps: list[Step] = Field(default_factory=list)


class ProfileConfig(CamelModel):
    schema_version: Literal["v0.2"] = Field(default="v0.2", alias="schemaVersion")
    prepare: StageConfig = Field(default_factory=StageConfig)
    test: StageConfig = Field(default_factory=StageConfig)
    run: dict[str, ReactiveServiceConfig | ManagedServiceConfig] = Field(
        default_factory=dict
    )

    def to_yaml(self, *, by_alias: bool = True, exclude_none: bool = True) -> str:
        data = self.model_dump(
            by_alias=by_alias, exclude_none=exclude_none, mode="json"
        )
        return yaml.safe_dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


class StepBuilder:
    def __init__(self, command: str, name: str | None = None):
        self._command = command
        self._name = name

    def build(self) -> Step:
        return Step(command=self._command, name=self._name)


class PortBuilder:
    def __init__(self, port: int):
        self._port = port
        self._is_public = False

    def public(self, is_public: bool = True) -> PortBuilder:
        self._is_public = is_public
        return self

    def build(self) -> PortConfig:
        return PortConfig(port=self._port, is_public=self._is_public)


class PathBuilder:
    def __init__(self, path: str, port: int):
        self._path = path
        self._port = port
        self._strip_path: bool | None = None

    def strip_path(self, strip: bool = True) -> PathBuilder:
        self._strip_path = strip
        return self

    def build(self) -> PathConfig:
        return PathConfig(port=self._port, path=self._path, strip_path=self._strip_path)


class ReactiveServiceBuilder:
    def __init__(self, name: str):
        self._name = name
        self._steps: list[Step] = []
        self._env: dict[str, str] = {}
        self._plan: int | None = None
        self._replicas: int = 1
        self._base_image: str | None = None
        self._run_as_user: int | None = None
        self._run_as_group: int | None = None
        self._mount_sub_path: str | None = None
        self._health_endpoint: str | None = None
        self._ports: list[PortConfig] = []
        self._paths: list[PathConfig] = []

    @property
    def name(self) -> str:
        return self._name

    def add_step(self, command: str, name: str | None = None) -> ReactiveServiceBuilder:
        self._steps.append(Step(command=command, name=name))
        return self

    def env(self, key: str, value: str) -> ReactiveServiceBuilder:
        self._env[key] = value
        return self

    def envs(self, env_vars: dict[str, str]) -> ReactiveServiceBuilder:
        self._env.update(env_vars)
        return self

    def plan(self, plan_id: int) -> ReactiveServiceBuilder:
        self._plan = plan_id
        return self

    def replicas(self, count: int) -> ReactiveServiceBuilder:
        self._replicas = max(1, count)
        return self

    def base_image(self, image: str) -> ReactiveServiceBuilder:
        self._base_image = image
        return self

    def run_as(
        self, user: int | None = None, group: int | None = None
    ) -> ReactiveServiceBuilder:
        self._run_as_user = user
        self._run_as_group = group
        return self

    def mount_sub_path(self, path: str) -> ReactiveServiceBuilder:
        self._mount_sub_path = path
        return self

    def health_endpoint(self, endpoint: str) -> ReactiveServiceBuilder:
        self._health_endpoint = endpoint
        return self

    def add_port(self, port: int, *, public: bool = False) -> ReactiveServiceBuilder:
        self._ports.append(PortConfig(port=port, is_public=public))
        return self

    def add_path(
        self, path: str, port: int, *, strip_path: bool | None = None
    ) -> ReactiveServiceBuilder:
        self._paths.append(PathConfig(port=port, path=path, strip_path=strip_path))
        return self

    def build(self) -> tuple[str, ReactiveServiceConfig]:
        if self._plan is None:
            raise ValueError(
                f"Service '{self._name}' requires a plan ID. "
                "Use .plan(plan_id) to set it."
            )

        network = None
        if self._ports or self._paths:
            network = NetworkConfig(ports=self._ports, paths=self._paths)

        config = ReactiveServiceConfig(
            steps=self._steps,
            plan=self._plan,
            replicas=self._replicas,
            env=self._env if self._env else None,
            base_image=self._base_image,
            run_as_user=self._run_as_user,
            run_as_group=self._run_as_group,
            mount_sub_path=self._mount_sub_path,
            health_endpoint=self._health_endpoint,
            network=network,
        )
        return self._name, config


class ManagedServiceBuilder:
    def __init__(self, name: str, provider: str, plan: str):
        self._name = name
        self._provider = provider
        self._plan = plan
        self._config: dict[str, Any] = {}
        self._secrets: dict[str, str] = {}

    @property
    def name(self) -> str:
        return self._name

    def config(self, key: str, value: Any) -> ManagedServiceBuilder:
        self._config[key] = value
        return self

    def configs(self, config: dict[str, Any]) -> ManagedServiceBuilder:
        self._config.update(config)
        return self

    def secret(self, key: str, value: str) -> ManagedServiceBuilder:
        self._secrets[key] = value
        return self

    def secrets(self, secrets: dict[str, str]) -> ManagedServiceBuilder:
        self._secrets.update(secrets)
        return self

    def build(self) -> tuple[str, ManagedServiceConfig]:
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
        self._prepare_steps: list[Step] = []
        self._test_steps: list[Step] = []
        self._services: dict[str, ReactiveServiceConfig | ManagedServiceConfig] = {}
        self._current_service: Any | None = None

    def prepare(self) -> PrepareStageBuilder:
        return PrepareStageBuilder(self)

    def test(self) -> TestStageBuilder:
        return TestStageBuilder(self)

    def add_reactive_service(self, name: str) -> ReactiveServiceBuilderContext:
        self._finalize_current_service()
        self._current_service = ReactiveServiceBuilderContext(self, name)
        return self._current_service

    def add_managed_service(
        self, name: str, *, provider: str, plan: str
    ) -> ManagedServiceBuilderContext:
        self._finalize_current_service()
        self._current_service = ManagedServiceBuilderContext(self, name, provider, plan)
        return self._current_service

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown methods to the current service builder."""
        if self._current_service is not None and hasattr(self._current_service, name):
            method = getattr(self._current_service, name)
            if callable(method):

                def wrapper(*args: Any, **kwargs: Any) -> ProfileBuilder:
                    method(*args, **kwargs)
                    return self

                return wrapper
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    def _finalize_current_service(self) -> None:
        if self._current_service is not None:
            name, config = self._current_service._builder.build()
            self._services[name] = config
            self._current_service = None

    def build(self) -> ProfileConfig:
        """Build the final profile configuration."""
        self._finalize_current_service()
        return ProfileConfig(
            prepare=StageConfig(steps=self._prepare_steps),
            test=StageConfig(steps=self._test_steps),
            run=self._services,
        )


class PrepareStageBuilder:
    def __init__(self, parent: ProfileBuilder):
        self._parent = parent

    def add_step(self, command: str, name: str | None = None) -> PrepareStageBuilder:
        self._parent._prepare_steps.append(Step(command=command, name=name))
        return self

    def done(self) -> ProfileBuilder:
        return self._parent


class TestStageBuilder:
    def __init__(self, parent: ProfileBuilder):
        self._parent = parent

    def add_step(self, command: str, name: str | None = None) -> TestStageBuilder:
        self._parent._test_steps.append(Step(command=command, name=name))
        return self

    def done(self) -> ProfileBuilder:
        return self._parent


class ReactiveServiceBuilderContext:
    def __init__(self, parent: ProfileBuilder, name: str):
        self._parent = parent
        self._builder = ReactiveServiceBuilder(name)

    def add_step(
        self, command: str, name: str | None = None
    ) -> ReactiveServiceBuilderContext:
        self._builder.add_step(command, name)
        return self

    def env(self, key: str, value: str) -> ReactiveServiceBuilderContext:
        self._builder.env(key, value)
        return self

    def envs(self, env_vars: dict[str, str]) -> ReactiveServiceBuilderContext:
        self._builder.envs(env_vars)
        return self

    def plan(self, plan_id: int) -> ReactiveServiceBuilderContext:
        self._builder.plan(plan_id)
        return self

    def replicas(self, count: int) -> ReactiveServiceBuilderContext:
        self._builder.replicas(count)
        return self

    def base_image(self, image: str) -> ReactiveServiceBuilderContext:
        self._builder.base_image(image)
        return self

    def run_as(
        self, user: int | None = None, group: int | None = None
    ) -> ReactiveServiceBuilderContext:
        self._builder.run_as(user, group)
        return self

    def mount_sub_path(self, path: str) -> ReactiveServiceBuilderContext:
        self._builder.mount_sub_path(path)
        return self

    def health_endpoint(self, endpoint: str) -> ReactiveServiceBuilderContext:
        self._builder.health_endpoint(endpoint)
        return self

    def add_port(
        self, port: int, *, public: bool = False
    ) -> ReactiveServiceBuilderContext:
        self._builder.add_port(port, public=public)
        return self

    def add_path(
        self, path: str, port: int, *, strip_path: bool | None = None
    ) -> ReactiveServiceBuilderContext:
        self._builder.add_path(path, port, strip_path=strip_path)
        return self

    def done(self) -> ProfileBuilder:
        name, config = self._builder.build()
        self._parent._services[name] = config
        return self._parent


class ManagedServiceBuilderContext:
    def __init__(self, parent: ProfileBuilder, name: str, provider: str, plan: str):
        self._parent = parent
        self._builder = ManagedServiceBuilder(name, provider, plan)

    def config(self, key: str, value: Any) -> ManagedServiceBuilderContext:
        self._builder.config(key, value)
        return self

    def configs(self, config: dict[str, Any]) -> ManagedServiceBuilderContext:
        self._builder.configs(config)
        return self

    def secret(self, key: str, value: str) -> ManagedServiceBuilderContext:
        self._builder.secret(key, value)
        return self

    def secrets(self, secrets: dict[str, str]) -> ManagedServiceBuilderContext:
        self._builder.secrets(secrets)
        return self

    def done(self) -> ProfileBuilder:
        name, config = self._builder.build()
        self._parent._services[name] = config
        return self._parent
