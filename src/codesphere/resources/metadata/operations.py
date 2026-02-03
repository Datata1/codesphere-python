from ...core.base import ResourceList
from ...core.operations import APIOperation
from .schemas import Datacenter, Image, WsPlan

_LIST_DC_OP = APIOperation(
    method="GET",
    endpoint_template="/metadata/datacenters",
    input_model=type(None),
    response_model=ResourceList[Datacenter],
)

_LIST_PLANS_OP = APIOperation(
    method="GET",
    endpoint_template="/metadata/workspace-plans",
    input_model=type(None),
    response_model=ResourceList[WsPlan],
)

_LIST_IMAGES_OP = APIOperation(
    method="GET",
    endpoint_template="/metadata/workspace-base-images",
    input_model=type(None),
    response_model=ResourceList[Image],
)
