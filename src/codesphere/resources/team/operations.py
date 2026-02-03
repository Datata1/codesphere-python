from .schemas import Team, TeamCreate
from ...core.base import ResourceList
from ...core.operations import APIOperation

_LIST_TEAMS_OP = APIOperation(
    method="GET",
    endpoint_template="/teams",
    input_model=type(None),
    response_model=ResourceList[Team],
)

_GET_TEAM_OP = APIOperation(
    method="GET",
    endpoint_template="/teams/{team_id}",
    input_model=type(None),
    response_model=Team,
)

_CREATE_TEAM_OP = APIOperation(
    method="POST",
    endpoint_template="/teams",
    input_model=TeamCreate,
    response_model=Team,
)
