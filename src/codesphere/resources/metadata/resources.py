from typing import Awaitable, Callable, List
from ..base import ResourceBase, APIOperation
from .models import Datacenters, WsPlans, Images


class MetadataResource(ResourceBase):
    """Contains all API operations for team ressources."""

    datacenters: Callable[[], Awaitable[List[Datacenters]]]
    datacenters = APIOperation(
        method="GET",
        endpoint_template="/metadata/datacenters",
        input_model=None,
        response_model=List[Datacenters],
    )

    plans: Callable[[], Awaitable[List[WsPlans]]]
    plans = APIOperation(
        method="GET",
        endpoint_template="/metadata/workspace-plans",
        input_model=None,
        response_model=List[WsPlans],
    )

    images: Callable[[], Awaitable[List[Images]]]
    images = APIOperation(
        method="GET",
        endpoint_template="/metadata/workspace-base-images",
        input_model=None,
        response_model=List[Images],
    )
