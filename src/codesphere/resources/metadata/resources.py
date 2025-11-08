"""
Defines the resource class for the Metadata API endpoints.
"""

from typing import List
from ...core import APIOperation, AsyncCallable
from ...core import ResourceBase
from .models import Datacenter, WsPlan, Image


class MetadataResource(ResourceBase):
    list_datacenters: AsyncCallable[List[Datacenter]]
    """Fetches a list of all available data centers."""
    list_datacenters = APIOperation(
        method="GET",
        endpoint_template="/metadata/datacenters",
        input_model=None,
        response_model=List[Datacenter],
    )

    list_plans: AsyncCallable[List[WsPlan]]
    """Fetches a list of all available workspace plans."""
    list_plans = APIOperation(
        method="GET",
        endpoint_template="/metadata/workspace-plans",
        input_model=None,
        response_model=List[WsPlan],
    )

    list_images: AsyncCallable[List[Image]]
    """Fetches a list of all available workspace base images."""
    list_images = APIOperation(
        method="GET",
        endpoint_template="/metadata/workspace-base-images",
        input_model=None,
        response_model=List[Image],
    )
