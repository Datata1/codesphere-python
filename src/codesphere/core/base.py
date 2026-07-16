"""Compatibility shim; implementations live in codesphere._async.core.base
(client-bound bases) and codesphere.core.models (shared pydantic bases)."""

from .._async.core.base import (
    BoundModel,
    ResourceBase,
    TeamScopedResource,
    WorkspaceScopedResource,
)
from .models import CamelModel, ResourceList

__all__ = [
    "BoundModel",
    "CamelModel",
    "ResourceBase",
    "ResourceList",
    "TeamScopedResource",
    "WorkspaceScopedResource",
]
