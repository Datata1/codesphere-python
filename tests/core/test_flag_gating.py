"""Operation gating via APIOperation.required_flag (pre-request fail-fast)."""

import asyncio

import pytest

from codesphere import (
    FeatureNotAvailableError,
    FeatureNotEnabledError,
)
from codesphere.core.base import BoundModel, ResourceBase
from codesphere.core.operations import APIOperation
from codesphere.feature_flags import FlagCategory, FlagRequirement


class Gadget(BoundModel):
    id: int


GATED_OP = APIOperation(
    method="GET",
    endpoint_template="/gadgets/{gadget_id}",
    response_model=Gadget,
    required_flag=FlagRequirement("gadgets", FlagCategory.PREVIEW),
)


class GadgetsResource(ResourceBase):
    async def get(self, gadget_id: int) -> Gadget:
        return await self._execute(GATED_OP, gadget_id=gadget_id)


FLAGS_ENABLED = {"preview": {"available": ["gadgets"], "enabled": ["gadgets"]}}
FLAGS_DISABLED = {"preview": {"available": ["gadgets"], "enabled": []}}
FLAGS_MISSING = {"preview": {"available": [], "enabled": []}}


@pytest.fixture
def gadgets(sdk):
    return GadgetsResource(sdk._http_client)


class TestOperationGating:
    async def test_enabled_flag_lets_the_call_through(self, gadgets, mock_api):
        mock_api.get("/ide-service/flags").respond(200, json=FLAGS_ENABLED)
        route = mock_api.get("/gadgets/1").respond(200, json={"id": 1})

        gadget = await gadgets.get(1)

        assert gadget.id == 1
        assert route.call_count == 1

    async def test_disabled_flag_fails_before_any_request(self, gadgets, mock_api):
        mock_api.get("/ide-service/flags").respond(200, json=FLAGS_DISABLED)
        route = mock_api.get("/gadgets/1").respond(200, json={"id": 1})

        with pytest.raises(FeatureNotEnabledError) as exc_info:
            await gadgets.get(1)

        assert route.called is False  # nothing was sent to the gated endpoint
        assert exc_info.value.flag == "gadgets"
        assert exc_info.value.category == "preview"

    async def test_unavailable_flag_raises_not_available(self, gadgets, mock_api):
        mock_api.get("/ide-service/flags").respond(200, json=FLAGS_MISSING)
        route = mock_api.get("/gadgets/1").respond(200, json={"id": 1})

        with pytest.raises(FeatureNotAvailableError):
            await gadgets.get(1)
        assert route.called is False

    async def test_legacy_platform_404_fails_closed_with_hint(self, gadgets, mock_api):
        mock_api.get("/ide-service/flags").respond(404, json={})

        with pytest.raises(FeatureNotAvailableError, match="predate feature flags"):
            await gadgets.get(1)

    async def test_flags_fetched_once_across_gated_calls(self, gadgets, mock_api):
        flags_route = mock_api.get("/ide-service/flags").respond(
            200, json=FLAGS_ENABLED
        )
        mock_api.get(url__regex=r".*/gadgets/\d+").respond(200, json={"id": 1})

        await gadgets.get(1)
        await gadgets.get(2)
        await asyncio.gather(gadgets.get(3), gadgets.get(4), gadgets.get(5))

        assert flags_route.call_count == 1

    async def test_refresh_unlocks_a_newly_enabled_flag(self, sdk, gadgets, mock_api):
        flags_route = mock_api.get("/ide-service/flags")
        flags_route.side_effect = [
            httpx_response(200, FLAGS_DISABLED),
            httpx_response(200, FLAGS_ENABLED),
        ]
        mock_api.get("/gadgets/1").respond(200, json={"id": 1})

        with pytest.raises(FeatureNotEnabledError):
            await gadgets.get(1)

        await sdk.flags.refresh()
        gadget = await gadgets.get(1)
        assert gadget.id == 1


def httpx_response(status: int, json_body: dict):
    import httpx

    return httpx.Response(status, json=json_body)


class TestRequireFlagHelper:
    async def test_resource_base_helper(self, sdk, mock_api):
        mock_api.get("/ide-service/flags").respond(200, json=FLAGS_ENABLED)
        resource = GadgetsResource(sdk._http_client)

        await resource._require_flag(
            FlagRequirement("gadgets", FlagCategory.PREVIEW)
        )  # enabled -> no raise
        with pytest.raises(FeatureNotAvailableError):
            await resource._require_flag(FlagRequirement("other", FlagCategory.PREVIEW))

    async def test_bound_model_helper(self, sdk, mock_api):
        mock_api.get("/ide-service/flags").respond(200, json=FLAGS_ENABLED)
        gadget = Gadget(id=1)
        gadget._http_client = sdk._http_client

        await gadget._require_flag(FlagRequirement("gadgets", FlagCategory.PREVIEW))

    async def test_detached_bound_model_raises_runtime_error(self):
        gadget = Gadget(id=1)
        with pytest.raises(RuntimeError, match="detached model"):
            await gadget._require_flag(FlagRequirement("gadgets", FlagCategory.PREVIEW))
