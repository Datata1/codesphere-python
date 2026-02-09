from ....core.operations import APIOperation

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
