from ....core.base import ResourceList
from ....core.operations import APIOperation
from .schemas import (
    CustomDomainConfig,
    DomainBase,
    DomainVerificationStatus,
)

_LIST_OP = APIOperation(
    method="GET",
    endpoint_template="/domains/team/{team_id}",
    response_model=ResourceList[DomainBase],
)

_GET_OP = APIOperation(
    method="GET",
    endpoint_template="/domains/team/{team_id}/domain/{name}",
    response_model=DomainBase,
)

_CREATE_OP = APIOperation(
    method="POST",
    endpoint_template="/domains/team/{team_id}/domain/{name}",
    response_model=DomainBase,
)

_UPDATE_OP = APIOperation(
    method="PATCH",
    endpoint_template="/domains/team/{team_id}/domain/{name}",
    input_model=CustomDomainConfig,
    response_model=DomainBase,
)

_UPDATE_WS_OP = APIOperation(
    method="PUT",
    endpoint_template="/domains/team/{team_id}/domain/{name}/workspace-connections",
    input_model=None,
    response_model=DomainBase,
)

_VERIFY_OP = APIOperation(
    method="POST",
    endpoint_template="/domains/team/{team_id}/domain/{name}/verify",
    response_model=DomainVerificationStatus,
)

_DELETE_OP = APIOperation(
    method="DELETE",
    endpoint_template="/domains/team/{team_id}/domain/{name}",
    response_model=DomainBase,
)
