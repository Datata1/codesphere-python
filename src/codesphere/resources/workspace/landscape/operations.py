from ....core.operations import APIOperation
from .schemas import PipelineStatusList

_DEPLOY_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/landscape/deploy",
    response_model=type(None),
)

_DEPLOY_WITH_PROFILE_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/landscape/deploy/{profile}",
    response_model=type(None),
)

_TEARDOWN_OP = APIOperation(
    method="DELETE",
    endpoint_template="/workspaces/{id}/landscape/teardown",
    response_model=type(None),
)

_SCALE_OP = APIOperation(
    method="PATCH",
    endpoint_template="/workspaces/{id}/landscape/scale",
    response_model=type(None),
)

# Pipeline operations
_START_PIPELINE_STAGE_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/pipeline/{stage}/start",
    response_model=type(None),
)

_START_PIPELINE_STAGE_WITH_PROFILE_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/pipeline/{stage}/start/{profile}",
    response_model=type(None),
)

_STOP_PIPELINE_STAGE_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/pipeline/{stage}/stop",
    response_model=type(None),
)

_GET_PIPELINE_STATUS_OP = APIOperation(
    method="GET",
    endpoint_template="/workspaces/{id}/pipeline/{stage}",
    response_model=PipelineStatusList,
)
