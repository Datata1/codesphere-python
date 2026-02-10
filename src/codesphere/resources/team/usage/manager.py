from __future__ import annotations

from datetime import datetime
from functools import partial
from typing import AsyncIterator, Union

from pydantic import Field

from ....core.handler import _APIOperationExecutor
from ....core.operations import AsyncCallable
from ....http_client import APIHttpClient
from .operations import _GET_LANDSCAPE_EVENTS_OP, _GET_LANDSCAPE_SUMMARY_OP
from .schemas import (
    LandscapeServiceEvent,
    LandscapeServiceSummary,
    UsageEventsResponse,
    UsageSummaryResponse,
)


class TeamUsageManager(_APIOperationExecutor):
    """Manager for team usage history operations.

    Provides access to landscape service usage summaries and events with
    support for pagination and automatic iteration through all results.

    Example:
        ```python
        summary = await team.usage.get_landscape_summary(
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            limit=50
        )
        print(f"Total items: {summary.total_items}")
        print(f"Page {summary.current_page} of {summary.total_pages}")

        for item in summary.items:
            print(f"{item.resource_name}: {item.usage_seconds}s")

        await summary.refresh()

        async for item in team.usage.iter_all_landscape_summary(
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        ):
            print(f"{item.resource_name}: {item.usage_seconds}s")
        ```
    """

    def __init__(self, http_client: APIHttpClient, team_id: int):
        self._http_client = http_client
        self.team_id = team_id

    get_landscape_summary_op: AsyncCallable[UsageSummaryResponse] = Field(
        default=_GET_LANDSCAPE_SUMMARY_OP, exclude=True
    )

    async def get_landscape_summary(
        self,
        begin_date: Union[datetime, str],
        end_date: Union[datetime, str],
        limit: int = 25,
        offset: int = 0,
    ) -> UsageSummaryResponse:
        params = {
            "beginDate": begin_date.isoformat()
            if isinstance(begin_date, datetime)
            else begin_date,
            "endDate": end_date.isoformat()
            if isinstance(end_date, datetime)
            else end_date,
            "limit": min(max(1, limit), 100),
            "offset": max(0, offset),
        }
        result: UsageSummaryResponse = await self.get_landscape_summary_op(
            params=params
        )

        result._refresh_op = partial(self.get_landscape_summary_op)
        result._team_id = self.team_id

        return result

    async def iter_all_landscape_summary(
        self,
        begin_date: Union[datetime, str],
        end_date: Union[datetime, str],
        page_size: int = 100,
    ) -> AsyncIterator[LandscapeServiceSummary]:
        offset = 0
        page_size = min(max(1, page_size), 100)

        while True:
            response = await self.get_landscape_summary(
                begin_date=begin_date,
                end_date=end_date,
                limit=page_size,
                offset=offset,
            )

            for item in response.items:
                yield item

            if not response.has_next_page:
                break

            offset += page_size

    get_landscape_events_op: AsyncCallable[UsageEventsResponse] = Field(
        default=_GET_LANDSCAPE_EVENTS_OP, exclude=True
    )

    async def get_landscape_events(
        self,
        resource_id: str,
        begin_date: Union[datetime, str],
        end_date: Union[datetime, str],
        limit: int = 25,
        offset: int = 0,
    ) -> UsageEventsResponse:
        params = {
            "beginDate": begin_date.isoformat()
            if isinstance(begin_date, datetime)
            else begin_date,
            "endDate": end_date.isoformat()
            if isinstance(end_date, datetime)
            else end_date,
            "limit": min(max(1, limit), 100),
            "offset": max(0, offset),
        }
        result: UsageEventsResponse = await self.get_landscape_events_op(
            resource_id=resource_id, params=params
        )

        result._refresh_op = partial(
            self.get_landscape_events_op, resource_id=resource_id
        )
        result._team_id = self.team_id
        result._resource_id = resource_id

        return result

    async def iter_all_landscape_events(
        self,
        resource_id: str,
        begin_date: Union[datetime, str],
        end_date: Union[datetime, str],
        page_size: int = 100,
    ) -> AsyncIterator[LandscapeServiceEvent]:
        offset = 0
        page_size = min(max(1, page_size), 100)

        while True:
            response = await self.get_landscape_events(
                resource_id=resource_id,
                begin_date=begin_date,
                end_date=end_date,
                limit=page_size,
                offset=offset,
            )

            for item in response.items:
                yield item

            if not response.has_next_page:
                break

            offset += page_size
