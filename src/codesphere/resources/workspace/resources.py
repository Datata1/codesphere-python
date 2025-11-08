from typing import List, Protocol

from ...core import APIOperation, ResourceBase
from .models import Workspace, WorkspaceCreate


class ListWorkspacesCallable(Protocol):
    async def __call__(self, *, team_id: int) -> List[Workspace]: ...


class GetWorkspaceCallable(Protocol):
    async def __call__(self, *, workspace_id: int) -> Workspace: ...


class CreateWorkspaceCallable(Protocol):
    async def __call__(self, *, data: WorkspaceCreate) -> Workspace: ...


class WorkspacesResource(ResourceBase):
    """Manages all API operations for the Workspace resource."""

    list_by_team: ListWorkspacesCallable
    """
    Lists all workspaces for a specific team.

    Args:
        team_id (int): The unique identifier for the team.

    Returns:
        List[Workspace]: A list of Workspace objects associated with the team.
    """
    list_by_team = APIOperation(
        method="GET",
        endpoint_template="/workspaces/team/{team_id}",
        response_model=List[Workspace],
    )

    get: GetWorkspaceCallable
    """
    Fetches a single workspace by its ID.

    Args:
        workspace_id (int): The unique identifier for the workspace.

    Returns:
        Workspace: The requested Workspace object.
    """
    get = APIOperation(
        method="GET",
        endpoint_template="/workspaces/{workspace_id}",
        response_model=Workspace,
    )

    create: CreateWorkspaceCallable
    """
    Creates a new workspace.

    Args:
        data (WorkspaceCreate): The data payload for the new workspace.

    Returns:
        Workspace: The newly created Workspace object.
    """
    create = APIOperation(
        method="POST",
        endpoint_template="/workspaces",
        input_model=WorkspaceCreate,
        response_model=Workspace,
    )
