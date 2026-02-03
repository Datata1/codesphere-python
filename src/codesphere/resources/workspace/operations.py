from __future__ import annotations

from .command_schemas import CommandInput, CommandOutput, WorkspaceStatus
from .schemas import Workspace, WorkspaceCreate
from ...core.base import ResourceList
from ...core.operations import APIOperation

_LIST_BY_TEAM_OP = APIOperation(
    method="GET",
    endpoint_template="/workspaces/team/{team_id}",
    response_model=ResourceList[Workspace],
)

_GET_OP = APIOperation(
    method="GET",
    endpoint_template="/workspaces/{workspace_id}",
    response_model=Workspace,
)

_CREATE_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces",
    input_model=WorkspaceCreate,
    response_model=Workspace,
)

_UPDATE_OP = APIOperation(
    method="PATCH",
    endpoint_template="/workspaces/{id}",
    response_model=type(None),
)

_DELETE_OP = APIOperation(
    method="DELETE",
    endpoint_template="/workspaces/{id}",
    response_model=type(None),
)

_GET_STATUS_OP = APIOperation(
    method="GET",
    endpoint_template="/workspaces/{id}/status",
    response_model=WorkspaceStatus,
)

_EXECUTE_COMMAND_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/execute",
    input_model=CommandInput,
    response_model=CommandOutput,
)
