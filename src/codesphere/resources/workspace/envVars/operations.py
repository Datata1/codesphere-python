from .schemas import EnvVar
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
