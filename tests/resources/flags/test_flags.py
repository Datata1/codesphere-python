"""Tests for sdk.flags and the FlagsSnapshot model (respx transport policy)."""

import httpx
import pytest

from codesphere.exceptions import NetworkError
from codesphere.feature_flags import FlagCategory, FlagsSnapshot


@pytest.fixture
def sample_flags_data():
    """Real-world shaped payload (three categories, overlapping states)."""
    return {
        "internal": {
            "available": ["msd", "vpn", "gpu-plan", "maintenance-mode"],
            "enabled": ["msd", "vpn"],
        },
        "preview": {
            "available": ["workspace-ssh", "secret-management", "tcp-udp"],
            "enabled": ["workspace-ssh", "secret-management"],
        },
        "features": {
            "available": ["billing", "email-signin", "avatar-upload"],
            "enabled": ["email-signin"],
        },
    }


class TestFlagsSnapshot:
    def test_parses_payload(self, sample_flags_data):
        snapshot = FlagsSnapshot.model_validate(sample_flags_data)
        assert "msd" in snapshot.internal.available
        assert snapshot.preview.enabled == frozenset(
            {"workspace-ssh", "secret-management"}
        )

    def test_empty_snapshot_has_nothing(self):
        snapshot = FlagsSnapshot.empty()
        assert not snapshot.is_available("anything")
        assert not snapshot.is_enabled("anything")
        assert snapshot.categories_with("anything") == ()

    def test_union_lookup_across_categories(self, sample_flags_data):
        snapshot = FlagsSnapshot.model_validate(sample_flags_data)
        assert snapshot.is_enabled("workspace-ssh")  # lives in preview
        assert snapshot.is_enabled("msd")  # lives in internal
        assert snapshot.is_available("billing")
        assert not snapshot.is_enabled("billing")  # available but off

    def test_category_scoped_lookup(self, sample_flags_data):
        snapshot = FlagsSnapshot.model_validate(sample_flags_data)
        assert snapshot.is_enabled("msd", FlagCategory.INTERNAL)
        assert not snapshot.is_enabled("msd", FlagCategory.FEATURES)
        assert not snapshot.is_available("msd", FlagCategory.PREVIEW)

    def test_categories_with_reports_collisions(self, sample_flags_data):
        data = dict(sample_flags_data)
        data["features"] = {
            "available": [*data["features"]["available"], "msd"],
            "enabled": [],
        }
        snapshot = FlagsSnapshot.model_validate(data)
        assert snapshot.categories_with("msd") == (
            FlagCategory.INTERNAL,
            FlagCategory.FEATURES,
        )

    def test_snapshot_is_frozen(self, sample_flags_data):
        from pydantic import ValidationError

        snapshot = FlagsSnapshot.model_validate(sample_flags_data)
        with pytest.raises(ValidationError):
            snapshot.internal = snapshot.preview  # ty: ignore[invalid-assignment]


class TestFlagsResource:
    async def test_get_fetches_and_caches(self, sdk, mock_api, sample_flags_data):
        route = mock_api.get("/ide-service/flags").respond(200, json=sample_flags_data)

        first = await sdk.flags.get()
        second = await sdk.flags.get()

        assert first == second
        assert route.call_count == 1

    async def test_refresh_refetches(self, sdk, mock_api, sample_flags_data):
        route = mock_api.get("/ide-service/flags").respond(200, json=sample_flags_data)

        await sdk.flags.get()
        await sdk.flags.refresh()

        assert route.call_count == 2

    async def test_is_enabled_and_available(self, sdk, mock_api, sample_flags_data):
        mock_api.get("/ide-service/flags").respond(200, json=sample_flags_data)

        assert await sdk.flags.is_enabled("msd") is True
        assert await sdk.flags.is_enabled("billing") is False
        assert await sdk.flags.is_available("billing") is True
        assert await sdk.flags.is_available("nonexistent") is False

    async def test_404_yields_cached_empty_snapshot(self, sdk, mock_api):
        route = mock_api.get("/ide-service/flags").respond(404, json={})

        snapshot = await sdk.flags.get()
        again = await sdk.flags.get()

        assert snapshot == FlagsSnapshot.empty()
        assert again == snapshot
        assert route.call_count == 1  # 404 is cached, not retried

    async def test_transient_error_is_not_cached(
        self, sdk, mock_api, sample_flags_data
    ):
        route = mock_api.get("/ide-service/flags")
        route.side_effect = [
            httpx.ConnectError("refused"),
            httpx.Response(200, json=sample_flags_data),
        ]

        with pytest.raises(NetworkError):
            await sdk.flags.get()

        snapshot = await sdk.flags.get()  # second call succeeds
        assert snapshot.is_enabled("msd")
        assert route.call_count == 2

    async def test_require_passes_and_raises(self, sdk, mock_api, sample_flags_data):
        from codesphere import FeatureNotEnabledError

        mock_api.get("/ide-service/flags").respond(200, json=sample_flags_data)

        await sdk.flags.require("msd")  # enabled -> no raise
        with pytest.raises(FeatureNotEnabledError):
            await sdk.flags.require("billing", FlagCategory.FEATURES)
