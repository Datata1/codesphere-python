from __future__ import annotations

from functools import cached_property
from typing import Optional

from pydantic import Field

from ...core import APIOperation, AsyncCallable, _APIOperationExecutor
from ...core.base import CamelModel
from .domain.manager import TeamDomainManager
from .usage.manager import TeamUsageManager


class TeamCreate(CamelModel):
    name: str
    dc: int


class TeamBase(CamelModel):
    id: int
    name: str
    description: Optional[str] = None
    avatar_id: Optional[str] = None
    avatar_url: Optional[str] = None
    is_first: bool
    default_data_center_id: int
    role: Optional[int] = None


class Team(TeamBase, _APIOperationExecutor):
    delete: AsyncCallable[None]
    delete = Field(
        default=APIOperation(
            method="DELETE",
            endpoint_template="/teams/{id}",
            response_model=type(None),
        ),
        exclude=True,
    )

    @cached_property
    def domains(self) -> TeamDomainManager:
        http_client = self.validate_http_client()
        return TeamDomainManager(http_client, team_id=self.id)

    @cached_property
    def usage(self) -> TeamUsageManager:
        http_client = self.validate_http_client()
        return TeamUsageManager(http_client, team_id=self.id)
