import pytest
from dataclasses import dataclass
from typing import List, Type

from codesphere.resources.metadata import (
    Datacenter,
    WsPlan,
    Image,
)


@dataclass
class MetadataListTestCase:
    """Test case for metadata list operations."""

    name: str
    operation: str
    mock_response: List[dict]
    expected_count: int
    expected_type: Type


metadata_list_test_cases = [
    MetadataListTestCase(
        name="List datacenters returns Datacenter models",
        operation="list_datacenters",
        mock_response=[
            {"id": 1, "name": "EU-West", "city": "Frankfurt", "countryCode": "DE"},
            {"id": 2, "name": "US-East", "city": "New York", "countryCode": "US"},
        ],
        expected_count=2,
        expected_type=Datacenter,
    ),
    MetadataListTestCase(
        name="List plans returns WsPlan models",
        operation="list_plans",
        mock_response=[
            {
                "id": 1,
                "priceUsd": 0,
                "title": "Free",
                "deprecated": False,
                "characteristics": {
                    "id": 1,
                    "CPU": 0.5,
                    "GPU": 0,
                    "RAM": 512,
                    "SSD": 1,
                    "TempStorage": 0,
                    "onDemand": False,
                },
                "maxReplicas": 1,
            },
        ],
        expected_count=1,
        expected_type=WsPlan,
    ),
    MetadataListTestCase(
        name="List images returns Image models",
        operation="list_images",
        mock_response=[
            {
                "id": "ubuntu-22.04",
                "name": "Ubuntu 22.04",
                "supportedUntil": "2027-04-01T00:00:00Z",
            },
        ],
        expected_count=1,
        expected_type=Image,
    ),
]


class TestMetadataResource:
    """Tests for the MetadataResource class."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "case",
        metadata_list_test_cases,
        ids=[c.name for c in metadata_list_test_cases],
    )
    async def test_list_operations(
        self, case: MetadataListTestCase, metadata_resource_factory
    ):
        """Test metadata list operations return correct model types."""
        resource, mock_client = metadata_resource_factory(case.mock_response)

        method = getattr(resource, case.operation)
        result = await method()

        assert len(result) == case.expected_count
        for item in result:
            assert isinstance(item, case.expected_type)

    @pytest.mark.asyncio
    async def test_list_datacenters_empty(self, metadata_resource_factory):
        """List datacenters should handle empty response."""
        resource, _ = metadata_resource_factory([])
        result = await resource.list_datacenters()

        assert result == []

    @pytest.mark.asyncio
    async def test_datacenter_fields(self, metadata_resource_factory):
        """Datacenter model should have correct fields populated."""
        mock_data = [
            {"id": 1, "name": "EU-West", "city": "Frankfurt", "countryCode": "DE"}
        ]
        resource, _ = metadata_resource_factory(mock_data)

        result = await resource.list_datacenters()
        dc = result[0]

        assert dc.id == 1
        assert dc.name == "EU-West"
        assert dc.city == "Frankfurt"
        assert dc.country_code == "DE"

    @pytest.mark.asyncio
    async def test_plan_characteristics(self, metadata_resource_factory):
        """WsPlan should have nested Characteristic model."""
        mock_data = [
            {
                "id": 8,
                "priceUsd": 1500,
                "title": "Pro",
                "deprecated": False,
                "characteristics": {
                    "id": 8,
                    "CPU": 4.0,
                    "GPU": 0,
                    "RAM": 8192,
                    "SSD": 50,
                    "TempStorage": 10,
                    "onDemand": False,
                },
                "maxReplicas": 3,
            }
        ]
        resource, _ = metadata_resource_factory(mock_data)

        result = await resource.list_plans()
        plan = result[0]

        assert plan.id == 8
        assert plan.price_usd == 1500
        assert plan.characteristics.cpu == 4.0
        assert plan.characteristics.ram == 8192


class TestDatacenterSchema:
    """Tests for the Datacenter schema."""

    def test_create_from_camel_case(self):
        """Datacenter should be created from camelCase JSON."""
        data = {"id": 1, "name": "Test", "city": "Berlin", "countryCode": "DE"}
        dc = Datacenter.model_validate(data)

        assert dc.id == 1
        assert dc.country_code == "DE"

    def test_dump_to_camel_case(self):
        """Datacenter should dump to camelCase."""
        dc = Datacenter(id=1, name="Test", city="Berlin", country_code="DE")
        dumped = dc.model_dump(by_alias=True)

        assert "countryCode" in dumped
        assert dumped["countryCode"] == "DE"


class TestWsPlanSchema:
    """Tests for the WsPlan schema."""

    def test_nested_characteristics(self):
        """WsPlan should properly parse nested characteristics."""
        data = {
            "id": 1,
            "priceUsd": 0,
            "title": "Free",
            "deprecated": False,
            "characteristics": {
                "id": 1,
                "CPU": 0.5,
                "GPU": 0,
                "RAM": 512,
                "SSD": 1,
                "TempStorage": 0,
                "onDemand": False,
            },
            "maxReplicas": 1,
        }
        plan = WsPlan.model_validate(data)

        assert plan.characteristics.cpu == 0.5
        assert plan.characteristics.on_demand is False
