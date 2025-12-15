from .models import EnvVar
from ...workspace.schemas import CommandInput, CommandOutput, WorkspaceStatus
from ....core.base import ResourceList
from ....core.operations import APIOperation

_GET_OP = APIOperation(
    method="GET",
    endpoint_template="/workspaces/{id}/env-vars",
    response_model=ResourceList[EnvVar],
)

_BULK_SET_OP = APIOperation(
    method="PUT",
    endpoint_template="/workspaces/{id}/env-vars",
    response_model=type(None),
)

_BULK_DELETE_OP = APIOperation(
    method="DELETE",
    endpoint_template="/workspaces/{id}/env-vars",
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
