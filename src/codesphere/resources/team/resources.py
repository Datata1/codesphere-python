from typing import List
from ..base import ResourceBase, APIOperation
from .models import Team, TeamCreate


class TeamsResource(ResourceBase):
    """Contains all API operations for team ressources."""

    list = APIOperation(
        method="GET",
        endpoint_template="/teams",
        input_model=None,
        response_model=List[Team],
    )

    get = APIOperation(
        method="GET",
        endpoint_template="/teams/{team_id}",
        input_model=None,
        response_model=Team,
    )

    create = APIOperation(
        method="POST",
        endpoint_template="/teams",
        input_model=TeamCreate,
        response_model=Team,
    )

    delete = APIOperation(
        method="DELETE",
        endpoint_template="/teams/{team_id}",
        input_model=None,
        response_model=None,
    )
