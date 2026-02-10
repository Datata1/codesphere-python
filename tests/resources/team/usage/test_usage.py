from datetime import datetime

import pytest

from codesphere.resources.team.usage.manager import TeamUsageManager
from codesphere.resources.team.usage.schemas import (
    LandscapeServiceEvent,
    LandscapeServiceSummary,
    ServiceAction,
    UsageEventsResponse,
    UsageSummaryResponse,
)


@pytest.fixture
def sample_usage_summary_data():
    return {
        "totalItems": 3,
        "limit": 25,
        "offset": 0,
        "beginDate": "2024-01-01T00:00:00Z",
        "endDate": "2024-01-31T23:59:59Z",
        "summary": [
            {
                "resourceId": "resource-1",
                "resourceName": "api-service",
                "usageSeconds": 86400.0,
                "planName": "Pro",
                "alwaysOn": True,
                "replicas": 2,
                "type": "landscape-service",
            },
            {
                "resourceId": "resource-2",
                "resourceName": "worker-service",
                "usageSeconds": 43200.0,
                "planName": "Basic",
                "alwaysOn": False,
                "replicas": 1,
                "type": "landscape-service",
            },
            {
                "resourceId": "resource-3",
                "resourceName": "db-service",
                "usageSeconds": 172800.0,
                "planName": "Pro",
                "alwaysOn": True,
                "replicas": 3,
                "type": "landscape-service",
            },
        ],
    }


@pytest.fixture
def sample_usage_events_data():
    """Sample response data for landscape service events."""
    return {
        "totalItems": 4,
        "limit": 25,
        "offset": 0,
        "beginDate": "2024-01-01T00:00:00Z",
        "endDate": "2024-01-31T23:59:59Z",
        "events": [
            {
                "id": 1,
                "initiatorId": "user-123",
                "initiatorEmail": "user@example.com",
                "resourceId": "resource-1",
                "date": "2024-01-15T10:30:00Z",
                "action": "start",
                "alwaysOn": True,
                "replicas": 2,
                "serviceName": "api-service",
            },
            {
                "id": 2,
                "initiatorId": "user-123",
                "initiatorEmail": "user@example.com",
                "resourceId": "resource-1",
                "date": "2024-01-15T18:00:00Z",
                "action": "stop",
                "alwaysOn": True,
                "replicas": 2,
                "serviceName": "api-service",
            },
            {
                "id": 3,
                "initiatorId": "user-456",
                "initiatorEmail": "admin@example.com",
                "resourceId": "resource-1",
                "date": "2024-01-16T09:00:00Z",
                "action": "start",
                "alwaysOn": True,
                "replicas": 2,
                "serviceName": "api-service",
            },
            {
                "id": 4,
                "initiatorId": "user-456",
                "initiatorEmail": "admin@example.com",
                "resourceId": "resource-1",
                "date": "2024-01-16T17:30:00Z",
                "action": "stop",
                "alwaysOn": True,
                "replicas": 2,
                "serviceName": "api-service",
            },
        ],
    }


class TestLandscapeServiceSummary:
    def test_parse_summary_item(self):
        data = {
            "resourceId": "resource-1",
            "resourceName": "api-service",
            "usageSeconds": 86400.0,
            "planName": "Pro",
            "alwaysOn": True,
            "replicas": 2,
            "type": "landscape-service",
        }
        summary = LandscapeServiceSummary.model_validate(data)

        assert summary.resource_id == "resource-1"
        assert summary.resource_name == "api-service"
        assert summary.usage_seconds == 86400.0
        assert summary.plan_name == "Pro"
        assert summary.always_on is True
        assert summary.replicas == 2
        assert summary.type == "landscape-service"


class TestLandscapeServiceEvent:
    def test_parse_event_item(self):
        data = {
            "id": 1,
            "initiatorId": "user-123",
            "initiatorEmail": "user@example.com",
            "resourceId": "resource-1",
            "date": "2024-01-15T10:30:00Z",
            "action": "start",
            "alwaysOn": True,
            "replicas": 2,
            "serviceName": "api-service",
        }
        event = LandscapeServiceEvent.model_validate(data)

        assert event.id == 1
        assert event.initiator_id == "user-123"
        assert event.initiator_email == "user@example.com"
        assert event.resource_id == "resource-1"
        assert event.action == ServiceAction.START
        assert event.always_on is True
        assert event.replicas == 2
        assert event.service_name == "api-service"

    def test_action_enum_values(self):
        assert ServiceAction.START == "start"
        assert ServiceAction.STOP == "stop"


class TestPaginatedResponse:
    def test_has_next_page_true(self):
        response = UsageSummaryResponse(
            total_items=100,
            limit=25,
            offset=0,
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=[],
        )
        assert response.has_next_page is True

    def test_has_next_page_false(self):
        response = UsageSummaryResponse(
            total_items=100,
            limit=25,
            offset=75,
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=[],
        )
        assert response.has_next_page is False

    def test_has_prev_page(self):
        response = UsageSummaryResponse(
            total_items=100,
            limit=25,
            offset=25,
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=[],
        )
        assert response.has_prev_page is True

    def test_has_no_prev_page(self):
        response = UsageSummaryResponse(
            total_items=100,
            limit=25,
            offset=0,
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=[],
        )
        assert response.has_prev_page is False

    def test_current_page(self):
        response = UsageSummaryResponse(
            total_items=100,
            limit=25,
            offset=50,
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=[],
        )
        assert response.current_page == 3

    def test_total_pages(self):
        response = UsageSummaryResponse(
            total_items=100,
            limit=25,
            offset=0,
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=[],
        )
        assert response.total_pages == 4

    def test_total_pages_with_remainder(self):
        response = UsageSummaryResponse(
            total_items=101,
            limit=25,
            offset=0,
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=[],
        )
        assert response.total_pages == 5


class TestUsageSummaryResponse:
    def test_parse_full_response(self, sample_usage_summary_data):
        response = UsageSummaryResponse.model_validate(sample_usage_summary_data)

        assert response.total_items == 3
        assert response.limit == 25
        assert response.offset == 0
        assert len(response.summary) == 3
        assert len(response.items) == 3

    def test_items_property(self, sample_usage_summary_data):
        response = UsageSummaryResponse.model_validate(sample_usage_summary_data)

        assert response.items is response.summary
        assert isinstance(response.items[0], LandscapeServiceSummary)


class TestUsageEventsResponse:
    def test_parse_full_response(self, sample_usage_events_data):
        response = UsageEventsResponse.model_validate(sample_usage_events_data)

        assert response.total_items == 4
        assert response.limit == 25
        assert response.offset == 0
        assert len(response.events) == 4
        assert len(response.items) == 4

    def test_items_property(self, sample_usage_events_data):
        response = UsageEventsResponse.model_validate(sample_usage_events_data)

        assert response.items is response.events
        assert isinstance(response.items[0], LandscapeServiceEvent)


class TestTeamUsageManager:
    @pytest.fixture
    def usage_manager(self, mock_http_client_for_resource, sample_usage_summary_data):
        mock_client = mock_http_client_for_resource(sample_usage_summary_data)
        manager = TeamUsageManager(http_client=mock_client, team_id=12345)
        return manager, mock_client

    @pytest.mark.asyncio
    async def test_get_landscape_summary(
        self, mock_http_client_for_resource, sample_usage_summary_data
    ):
        mock_client = mock_http_client_for_resource(sample_usage_summary_data)
        manager = TeamUsageManager(http_client=mock_client, team_id=12345)

        result = await manager.get_landscape_summary(
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        assert isinstance(result, UsageSummaryResponse)
        assert result.total_items == 3
        assert len(result.items) == 3
        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_landscape_summary_with_pagination(
        self, mock_http_client_for_resource, sample_usage_summary_data
    ):
        mock_client = mock_http_client_for_resource(sample_usage_summary_data)
        manager = TeamUsageManager(http_client=mock_client, team_id=12345)

        await manager.get_landscape_summary(
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            limit=50,
            offset=25,
        )

        call_args = mock_client.request.call_args
        params = call_args.kwargs.get("params", {})
        assert params["limit"] == 50
        assert params["offset"] == 25

    @pytest.mark.asyncio
    async def test_get_landscape_summary_clamps_limit(
        self, mock_http_client_for_resource, sample_usage_summary_data
    ):
        mock_client = mock_http_client_for_resource(sample_usage_summary_data)
        manager = TeamUsageManager(http_client=mock_client, team_id=12345)

        await manager.get_landscape_summary(
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            limit=200,
        )
        call_args = mock_client.request.call_args
        assert call_args.kwargs["params"]["limit"] == 100

    @pytest.mark.asyncio
    async def test_get_landscape_events(
        self, mock_http_client_for_resource, sample_usage_events_data
    ):
        mock_client = mock_http_client_for_resource(sample_usage_events_data)
        manager = TeamUsageManager(http_client=mock_client, team_id=12345)

        result = await manager.get_landscape_events(
            resource_id="resource-1",
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        assert isinstance(result, UsageEventsResponse)
        assert result.total_items == 4
        assert len(result.items) == 4
        mock_client.request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_iter_all_landscape_summary(
        self, mock_http_client_for_resource, sample_usage_summary_data
    ):
        mock_client = mock_http_client_for_resource(sample_usage_summary_data)
        manager = TeamUsageManager(http_client=mock_client, team_id=12345)

        items = []
        async for item in manager.iter_all_landscape_summary(
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        ):
            items.append(item)

        assert len(items) == 3
        assert all(isinstance(item, LandscapeServiceSummary) for item in items)

    @pytest.mark.asyncio
    async def test_iter_all_landscape_events(
        self, mock_http_client_for_resource, sample_usage_events_data
    ):
        mock_client = mock_http_client_for_resource(sample_usage_events_data)
        manager = TeamUsageManager(http_client=mock_client, team_id=12345)

        items = []
        async for item in manager.iter_all_landscape_events(
            resource_id="resource-1",
            begin_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        ):
            items.append(item)

        assert len(items) == 4
        assert all(isinstance(item, LandscapeServiceEvent) for item in items)


class TestTeamUsageProperty:
    @pytest.mark.asyncio
    async def test_team_has_usage_property(self, team_model_factory):
        team, _ = team_model_factory()

        usage_manager = team.usage

        assert isinstance(usage_manager, TeamUsageManager)
        assert usage_manager.team_id == team.id
