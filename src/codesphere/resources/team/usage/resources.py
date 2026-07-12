from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from functools import partial

from ....core.base import TeamScopedResource
from .operations import _GET_LANDSCAPE_EVENTS_OP, _GET_LANDSCAPE_SUMMARY_OP
from .schemas import (
    LandscapeServiceEvent,
    LandscapeServiceSummary,
    UsageEventsResponse,
    UsageSummaryResponse,
)


def _clamp_page_size(value: int) -> int:
    """The usage API accepts page sizes between 1 and 100."""
    return min(max(1, value), 100)


class TeamUsageManager(TeamScopedResource):
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

    async def get_landscape_summary(
        self,
        begin_date: datetime | str,
        end_date: datetime | str,
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
            "limit": _clamp_page_size(limit),
            "offset": max(0, offset),
        }
        result = await self._execute(
            _GET_LANDSCAPE_SUMMARY_OP, team_id=self.team_id, params=params
        )

        result._refresh_op = partial(
            self._execute, _GET_LANDSCAPE_SUMMARY_OP, team_id=self.team_id
        )
        result._team_id = self.team_id

        return result

    async def iter_all_landscape_summary(
        self,
        begin_date: datetime | str,
        end_date: datetime | str,
        page_size: int = 100,
    ) -> AsyncIterator[LandscapeServiceSummary]:
        offset = 0
        page_size = _clamp_page_size(page_size)

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

    async def get_landscape_events(
        self,
        resource_id: str,
        begin_date: datetime | str,
        end_date: datetime | str,
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
            "limit": _clamp_page_size(limit),
            "offset": max(0, offset),
        }
        result = await self._execute(
            _GET_LANDSCAPE_EVENTS_OP,
            team_id=self.team_id,
            resource_id=resource_id,
            params=params,
        )

        result._refresh_op = partial(
            self._execute,
            _GET_LANDSCAPE_EVENTS_OP,
            team_id=self.team_id,
            resource_id=resource_id,
        )
        result._team_id = self.team_id
        result._resource_id = resource_id

        return result

    async def iter_all_landscape_events(
        self,
        resource_id: str,
        begin_date: datetime | str,
        end_date: datetime | str,
        page_size: int = 100,
    ) -> AsyncIterator[LandscapeServiceEvent]:
        offset = 0
        page_size = _clamp_page_size(page_size)

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
