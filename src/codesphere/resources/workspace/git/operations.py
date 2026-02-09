from __future__ import annotations

from ....core.operations import APIOperation
from .schema import GitHead

_GET_HEAD_OP = APIOperation(
    method="GET",
    endpoint_template="/workspaces/{id}/git/head",
    response_model=GitHead,
)

_PULL_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/git/pull",
    response_model=type(None),
)

_PULL_WITH_REMOTE_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/git/pull/{remote}",
    response_model=type(None),
)

_PULL_WITH_REMOTE_AND_BRANCH_OP = APIOperation(
    method="POST",
    endpoint_template="/workspaces/{id}/git/pull/{remote}/{branch}",
    response_model=type(None),
)
