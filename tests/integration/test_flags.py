import pytest

from codesphere import CodesphereSDK
from codesphere.feature_flags import FlagCategory, FlagsSnapshot

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestFlagsIntegration:
    async def test_flags_snapshot_has_three_categories(self, sdk_client: CodesphereSDK):
        snapshot = await sdk_client.flags.get()

        assert isinstance(snapshot, FlagsSnapshot)
        for category in FlagCategory:
            flags = snapshot.category(category)
            assert flags.enabled <= flags.available  # enabled is a subset

    async def test_snapshot_is_cached(self, sdk_client: CodesphereSDK):
        first = await sdk_client.flags.get()
        second = await sdk_client.flags.get()
        assert first is second
