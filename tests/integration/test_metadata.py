"""
Integration tests for Metadata resources.

These tests are read-only and safe to run against any environment.
"""

import pytest

from codesphere.resources.metadata import Datacenter, WsPlan, Image


pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


class TestMetadataIntegration:
    """Integration tests for metadata endpoints."""

    async def test_list_datacenters(self, sdk_client):
        """Should retrieve a list of available datacenters."""
        datacenters = await sdk_client.metadata.list_datacenters()

        assert isinstance(datacenters, list)
        assert len(datacenters) > 0
        assert all(isinstance(dc, Datacenter) for dc in datacenters)

        # Verify datacenter has expected fields
        first_dc = datacenters[0]
        assert first_dc.id is not None
        assert first_dc.name is not None
        assert first_dc.city is not None
        assert first_dc.country_code is not None

    async def test_list_plans(self, sdk_client):
        """Should retrieve a list of available workspace plans."""
        plans = await sdk_client.metadata.list_plans()

        assert isinstance(plans, list)
        assert len(plans) > 0
        assert all(isinstance(plan, WsPlan) for plan in plans)

        # Verify plan has expected fields
        first_plan = plans[0]
        assert first_plan.id is not None
        assert first_plan.title is not None
        assert first_plan.characteristics is not None
        assert first_plan.characteristics.cpu is not None
        assert first_plan.characteristics.ram is not None

    async def test_list_images(self, sdk_client):
        """Should retrieve a list of available base images."""
        images = await sdk_client.metadata.list_images()

        assert isinstance(images, list)
        assert len(images) > 0
        assert all(isinstance(img, Image) for img in images)

        # Verify image has expected fields
        first_image = images[0]
        assert first_image.id is not None
        assert first_image.name is not None
