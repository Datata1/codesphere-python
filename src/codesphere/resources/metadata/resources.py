from typing import List
from ..base import ResourceBase, APIOperation
from .models import Datacenters, WsPlans, Images


class MetadataResource(ResourceBase):
    """Contains all API operations for team ressources."""

    datacenters = APIOperation(
        method="GET",
        endpoint_template="/metadata/datacenters",
        input_model=None,
        response_model=List[Datacenters],
    )

    plans = APIOperation(
        method="GET",
        endpoint_template="/metadata/workspace-plans",
        input_model=None,
        response_model=List[WsPlans],
    )

    images = APIOperation(
        method="GET",
        endpoint_template="/metadata/workspace-base-images",
        input_model=None,
        response_model=List[Images],
    )
