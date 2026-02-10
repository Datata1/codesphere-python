from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Generic, List, Optional, TypeVar

from pydantic import Field

from ....core.base import CamelModel
from ....core.handler import _APIOperationExecutor
from ....core.operations import AsyncCallable


class ServiceAction(str, Enum):
    START = "start"
    STOP = "stop"


class LandscapeServiceSummary(CamelModel):
    resource_id: str
    resource_name: str
    usage_seconds: float
    plan_name: str
    always_on: bool
    replicas: int
    type: str


class LandscapeServiceEvent(CamelModel):
    id: int
    initiator_id: str
    initiator_email: str
    resource_id: str
    date: datetime
    action: ServiceAction
    always_on: bool
    replicas: int
    service_name: str


ItemT = TypeVar("ItemT")


class PaginatedResponse(CamelModel, Generic[ItemT]):
    total_items: int
    limit: Optional[int] = Field(default=25)
    offset: Optional[int] = Field(default=0)
    begin_date: datetime
    end_date: datetime

    @property
    def has_next_page(self) -> bool:
        current_limit = self.limit or 25
        current_offset = self.offset or 0
        return (current_offset + current_limit) < self.total_items

    @property
    def has_prev_page(self) -> bool:
        return (self.offset or 0) > 0

    @property
    def current_page(self) -> int:
        current_limit = self.limit or 25
        current_offset = self.offset or 0
        return (current_offset // current_limit) + 1

    @property
    def total_pages(self) -> int:
        current_limit = self.limit or 25
        if self.total_items == 0:
            return 1
        return (self.total_items + current_limit - 1) // current_limit


class UsageSummaryResponse(
    PaginatedResponse[LandscapeServiceSummary], _APIOperationExecutor
):
    summary: List[LandscapeServiceSummary] = Field(default_factory=list)
    _refresh_op: Optional[AsyncCallable[UsageSummaryResponse]] = None
    _team_id: Optional[int] = None

    @property
    def items(self) -> List[LandscapeServiceSummary]:
        return self.summary

    async def refresh(self) -> UsageSummaryResponse:
        if self._refresh_op is None:
            raise RuntimeError(
                "Refresh operation not available. Use manager methods instead."
            )
        result = await self._refresh_op(
            params={
                "beginDate": self.begin_date.isoformat(),
                "endDate": self.end_date.isoformat(),
                "limit": self.limit,
                "offset": self.offset,
            }
        )
        for field_name in result.model_fields_set:
            if field_name not in ("_refresh_op", "_team_id"):
                setattr(self, field_name, getattr(result, field_name))
        return self


class UsageEventsResponse(
    PaginatedResponse[LandscapeServiceEvent], _APIOperationExecutor
):
    events: List[LandscapeServiceEvent] = Field(default_factory=list)

    _refresh_op: Optional[AsyncCallable[UsageEventsResponse]] = None
    _team_id: Optional[int] = None
    _resource_id: Optional[str] = None

    @property
    def items(self) -> List[LandscapeServiceEvent]:
        return self.events

    async def refresh(self) -> UsageEventsResponse:
        if self._refresh_op is None:
            raise RuntimeError(
                "Refresh operation not available. Use manager methods instead."
            )
        result = await self._refresh_op(
            params={
                "beginDate": self.begin_date.isoformat(),
                "endDate": self.end_date.isoformat(),
                "limit": self.limit,
                "offset": self.offset,
            }
        )
        for field_name in result.model_fields_set:
            if field_name not in ("_refresh_op", "_team_id", "_resource_id"):
                setattr(self, field_name, getattr(result, field_name))
        return self
