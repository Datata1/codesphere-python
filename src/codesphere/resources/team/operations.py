from types import NoneType

from ...core.base import ResourceList
from ...core.operations import APIOperation
from .schemas import Team, TeamCreate

_LIST_TEAMS_OP = APIOperation(
    method="GET",
    endpoint_template="/teams",
    response_model=ResourceList[Team],
)

_GET_TEAM_OP = APIOperation(
    method="GET",
    endpoint_template="/teams/{team_id}",
    response_model=Team,
)

_CREATE_TEAM_OP = APIOperation(
    method="POST",
    endpoint_template="/teams",
    input_model=TeamCreate,
    response_model=Team,
)

_DELETE_TEAM_OP = APIOperation(
    method="DELETE",
    endpoint_template="/teams/{team_id}",
    response_model=NoneType,
)
