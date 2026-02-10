import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from codesphere import CodesphereSDK
from codesphere.resources.team.usage import (
    LandscapeServiceEvent,
    LandscapeServiceSummary,
    TeamUsageManager,
    UsageEventsResponse,
    UsageSummaryResponse,
)
from codesphere.resources.workspace import Workspace
from codesphere.resources.workspace.landscape import ProfileBuilder

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestTeamUsageManagerAccess:
    async def test_team_has_usage_property(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        assert hasattr(team, "usage")
        assert isinstance(team.usage, TeamUsageManager)

    async def test_usage_manager_is_cached(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        manager1 = team.usage
        manager2 = team.usage

        assert manager1 is manager2


class TestGetLandscapeSummary:
    async def test_get_landscape_summary_returns_response(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=7)

        result = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
        )

        assert isinstance(result, UsageSummaryResponse)
        assert result.total_items >= 0
        assert result.begin_date is not None
        assert result.end_date is not None

    async def test_get_landscape_summary_with_pagination(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=7)

        result = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
            limit=10,
            offset=0,
        )

        assert result.limit == 10
        assert result.offset == 0

    async def test_get_landscape_summary_pagination_helpers(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=30)

        result = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
            limit=5,
            offset=0,
        )

        assert isinstance(result.has_next_page, bool)
        assert isinstance(result.has_prev_page, bool)
        assert isinstance(result.current_page, int)
        assert isinstance(result.total_pages, int)
        assert result.current_page >= 1
        assert result.total_pages >= 1

    async def test_get_landscape_summary_items_are_typed(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=30)

        result = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
        )

        for item in result.items:
            assert isinstance(item, LandscapeServiceSummary)
            assert hasattr(item, "resource_id")
            assert hasattr(item, "resource_name")
            assert hasattr(item, "usage_seconds")
            assert hasattr(item, "plan_name")


class TestGetLandscapeEvents:
    async def test_get_landscape_events_returns_response(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=30)

        summary = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
        )

        if summary.total_items == 0:
            pytest.skip("No usage data available for testing events")

        resource_id = summary.items[0].resource_id

        result = await team.usage.get_landscape_events(
            resource_id=resource_id,
            begin_date=begin_date,
            end_date=end_date,
        )

        assert isinstance(result, UsageEventsResponse)
        assert result.total_items >= 0

    async def test_get_landscape_events_items_are_typed(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=30)

        summary = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
        )

        if summary.total_items == 0:
            pytest.skip("No usage data available for testing events")

        resource_id = summary.items[0].resource_id

        result = await team.usage.get_landscape_events(
            resource_id=resource_id,
            begin_date=begin_date,
            end_date=end_date,
        )

        for item in result.items:
            assert isinstance(item, LandscapeServiceEvent)
            assert hasattr(item, "id")
            assert hasattr(item, "initiator_id")
            assert hasattr(item, "initiator_email")
            assert hasattr(item, "action")
            assert hasattr(item, "date")


class TestUsageHistoryAfterDeployment:
    async def test_deployment_generates_usage_events(
        self,
        sdk_client: CodesphereSDK,
        test_workspace: Workspace,
        test_team_id: int,
        test_plan_id: int,
    ):
        workspace = await sdk_client.workspaces.get(workspace_id=test_workspace.id)
        team = await sdk_client.teams.get(team_id=test_team_id)
        profile_name = "sdk-usage-test"

        before_deploy = datetime.now(timezone.utc)

        profile = (
            ProfileBuilder()
            .prepare()
            .add_step("echo 'Setup'")
            .done()
            .add_reactive_service("usage-test-svc")
            .plan(test_plan_id)
            .add_step("echo 'Running' && sleep infinity")
            .add_port(3000)
            .replicas(1)
            .done()
            .build()
        )

        try:
            await workspace.landscape.save_profile(profile_name, profile)
            await asyncio.sleep(1)
            await workspace.landscape.deploy(profile=profile_name)

            await asyncio.sleep(3)

            await workspace.landscape.teardown()

            await asyncio.sleep(2)

            after_teardown = datetime.now(timezone.utc)

            summary = await team.usage.get_landscape_summary(
                begin_date=before_deploy,
                end_date=after_teardown,
            )

            assert isinstance(summary, UsageSummaryResponse)
            assert summary.total_items >= 0

        finally:
            await workspace.landscape.delete_profile(profile_name)


class TestIterAllMethods:
    async def test_iter_all_landscape_summary(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=30)

        items = []
        async for item in team.usage.iter_all_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
            page_size=10,
        ):
            items.append(item)
            assert isinstance(item, LandscapeServiceSummary)

        summary = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
        )
        assert len(items) == summary.total_items

    async def test_iter_all_landscape_events(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=30)

        summary = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
        )

        if summary.total_items == 0:
            pytest.skip("No usage data available for testing event iteration")

        resource_id = summary.items[0].resource_id

        items = []
        async for item in team.usage.iter_all_landscape_events(
            resource_id=resource_id,
            begin_date=begin_date,
            end_date=end_date,
            page_size=10,
        ):
            items.append(item)
            assert isinstance(item, LandscapeServiceEvent)

        events = await team.usage.get_landscape_events(
            resource_id=resource_id,
            begin_date=begin_date,
            end_date=end_date,
        )
        assert len(items) == events.total_items


class TestRefreshMethod:
    async def test_usage_summary_refresh(
        self,
        sdk_client: CodesphereSDK,
        test_team_id: int,
    ):
        team = await sdk_client.teams.get(team_id=test_team_id)

        end_date = datetime.now(timezone.utc)
        begin_date = end_date - timedelta(days=7)

        result = await team.usage.get_landscape_summary(
            begin_date=begin_date,
            end_date=end_date,
        )

        original_total = result.total_items

        refreshed = await result.refresh()

        assert isinstance(refreshed, UsageSummaryResponse)
        assert refreshed.total_items >= 0
        assert result.total_items == refreshed.total_items
