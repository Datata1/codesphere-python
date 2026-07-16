from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any, Generic, Self, TypeVar

import httpx
from pydantic import Field

from codesphere.models.usage import (
    LandscapeServiceEvent,
    LandscapeServiceSummary,
    ServiceAction,
)

from ....core.base import CamelModel

__all__ = [
    "LandscapeServiceEvent",
    "LandscapeServiceSummary",
    "PaginatedResponse",
    "ServiceAction",
    "UsageEventsResponse",
    "UsageSummaryResponse",
]

ItemT = TypeVar("ItemT")


class PaginatedResponse(CamelModel, Generic[ItemT]):
    total_items: int
    limit: int = 25
    offset: int = 0
    begin_date: datetime
    end_date: datetime

    # Loosely typed so the sync flavor (no Awaitable) shares the shape.
    _refresh_op: Callable[..., Any] | None = None

    @property
    def has_next_page(self) -> bool:
        return (self.offset + self.limit) < self.total_items

    @property
    def has_prev_page(self) -> bool:
        return self.offset > 0

    @property
    def current_page(self) -> int:
        return (self.offset // self.limit) + 1

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 1
        return (self.total_items + self.limit - 1) // self.limit

    async def refresh(self, *, timeout: httpx.Timeout | float | None = None) -> Self:
        """Re-fetch this page with the same query parameters, in place."""
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
            },
            timeout=timeout,
        )
        for field_name in result.model_fields_set:
            setattr(self, field_name, getattr(result, field_name))
        return self


class UsageSummaryResponse(PaginatedResponse[LandscapeServiceSummary]):
    summary: list[LandscapeServiceSummary] = Field(default_factory=list)
    _team_id: int | None = None

    @property
    def items(self) -> list[LandscapeServiceSummary]:
        return self.summary


class UsageEventsResponse(PaginatedResponse[LandscapeServiceEvent]):
    events: list[LandscapeServiceEvent] = Field(default_factory=list)

    _team_id: int | None = None
    _resource_id: str | None = None

    @property
    def items(self) -> list[LandscapeServiceEvent]:
        return self.events
