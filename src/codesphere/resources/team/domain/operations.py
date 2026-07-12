from types import NoneType

from ....core.base import ResourceList
from ....core.operations import APIOperation
from .schemas import CustomDomainConfig, Domain, DomainVerificationStatus

_LIST_OP = APIOperation(
    method="GET",
    endpoint_template="/domains/team/{team_id}",
    response_model=ResourceList[Domain],
)

_GET_OP = APIOperation(
    method="GET",
    endpoint_template="/domains/team/{team_id}/domain/{name}",
    response_model=Domain,
)

_CREATE_OP = APIOperation(
    method="POST",
    endpoint_template="/domains/team/{team_id}/domain/{name}",
    response_model=Domain,
)

_UPDATE_OP = APIOperation(
    method="PATCH",
    endpoint_template="/domains/team/{team_id}/domain/{name}",
    input_model=CustomDomainConfig,
    response_model=Domain,
)

_UPDATE_WS_OP = APIOperation(
    method="PUT",
    endpoint_template="/domains/team/{team_id}/domain/{name}/workspace-connections",
    response_model=Domain,
)

_VERIFY_OP = APIOperation(
    method="POST",
    endpoint_template="/domains/team/{team_id}/domain/{name}/verify",
    response_model=DomainVerificationStatus,
)

_DELETE_OP = APIOperation(
    method="DELETE",
    endpoint_template="/domains/team/{team_id}/domain/{name}",
    response_model=NoneType,
)
