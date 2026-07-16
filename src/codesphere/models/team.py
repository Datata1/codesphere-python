from __future__ import annotations

from ..core.models import CamelModel


class TeamCreate(CamelModel):
    name: str
    dc: int


class TeamBase(CamelModel):
    id: int
    name: str
    description: str | None = None
    avatar_id: str | None = None
    avatar_url: str | None = None
    is_first: bool
    default_data_center_id: int
    role: int | None = None
