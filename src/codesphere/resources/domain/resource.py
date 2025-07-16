from typing import List
from ..base import ResourceBase, APIOperation
from .models import Domain


class DomainsResource(ResourceBase):
    def __init__(self, http_client, team_id: str):
        super().__init__(http_client)
        self.team_id = team_id

    list = APIOperation(
        method="GET",
        endpoint_template="/domains/team/{team_id}",
        response_model=List[Domain],
    )

    get = APIOperation(
        method="GET",
        endpoint_template="/domains/team/{team_id}/{domain_name}",
        response_model=Domain,
    )
