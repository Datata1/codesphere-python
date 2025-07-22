from typing import List
from ..base import ResourceBase, APIOperation
from .models import Workspace, WorkspaceCreate, WorkspaceUpdate


class WorkspacesResource(ResourceBase):
    """Manages all API operations for the Workspace resource."""

    list_by_team = APIOperation(
        method="GET",
        endpoint_template="/workspaces/team/{team_id}",
        response_model=List[Workspace],
    )

    get = APIOperation(
        method="GET",
        endpoint_template="/workspaces/{workspace_id}",
        response_model=Workspace,
    )

    create = APIOperation(
        method="POST",
        endpoint_template="/workspaces",
        input_model=WorkspaceCreate,
        response_model=Workspace,
    )

    update = APIOperation(
        method="PATCH",
        endpoint_template="/workspaces/{workspace_id}",
        input_model=WorkspaceUpdate,
        response_model=None,
    )

    delete = APIOperation(
        method="DELETE",
        endpoint_template="/workspaces/{workspace_id}",
        response_model=None,
    )
