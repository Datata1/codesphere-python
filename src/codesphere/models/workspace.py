from __future__ import annotations

from ..core.models import CamelModel
from .env_vars import EnvVar


class WorkspaceCreate(CamelModel):
    team_id: int
    name: str
    plan_id: int
    base_image: str | None = None
    is_private_repo: bool = True
    replicas: int = 1
    git_url: str | None = None
    initial_branch: str | None = None
    clone_depth: int | None = None
    source_workspace_id: int | None = None
    welcome_message: str | None = None
    vpn_config: str | None = None
    restricted: bool | None = None
    env: list[EnvVar] | None = None


class WorkspaceBase(CamelModel):
    id: int
    team_id: int
    name: str
    plan_id: int
    is_private_repo: bool
    replicas: int
    base_image: str | None = None
    data_center_id: int
    user_id: int
    git_url: str | None = None
    initial_branch: str | None = None
    source_workspace_id: int | None = None
    welcome_message: str | None = None
    vpn_config: str | None = None
    restricted: bool


class WorkspaceUpdate(CamelModel):
    plan_id: int | None = None
    base_image: str | None = None
    name: str | None = None
    replicas: int | None = None
    vpn_config: str | None = None
    restricted: bool | None = None


class CommandInput(CamelModel):
    command: str
    env: dict[str, str] | None = None


class CommandOutput(CamelModel):
    command: str
    working_dir: str
    output: str
    error: str


class WorkspaceStatus(CamelModel):
    is_running: bool
