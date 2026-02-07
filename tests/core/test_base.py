import json
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from codesphere.core.base import CamelModel, ResourceBase, ResourceList


@dataclass
class CamelModelTestCase:
    name: str
    field_name: str
    expected_alias: str


camel_model_test_cases = [
    CamelModelTestCase(
        name="Simple snake_case to camelCase",
        field_name="team_id",
        expected_alias="teamId",
    ),
    CamelModelTestCase(
        name="Multiple underscores",
        field_name="default_data_center_id",
        expected_alias="defaultDataCenterId",
    ),
    CamelModelTestCase(
        name="Single word stays lowercase",
        field_name="name",
        expected_alias="name",
    ),
]


class TestCamelModel:
    def test_inherits_from_base_model(self):
        assert issubclass(CamelModel, BaseModel)

    def test_alias_generator_configured(self):
        assert CamelModel.model_config.get("alias_generator") is not None

    def test_populate_by_name_enabled(self):
        assert CamelModel.model_config.get("populate_by_name") is True

    @pytest.mark.parametrize(
        "case", camel_model_test_cases, ids=[c.name for c in camel_model_test_cases]
    )
    def test_camel_case_alias_generation(self, case: CamelModelTestCase):
        """Test that snake_case fields are aliased to camelCase."""
        from pydantic import create_model

        DynamicModel = create_model(
            "DynamicModel", __base__=CamelModel, **{case.field_name: (str, "test")}
        )

        field_info = DynamicModel.model_fields[case.field_name]
        assert field_info.alias == case.expected_alias

    def test_model_dump_by_alias(self):
        class SampleModel(CamelModel):
            team_id: int
            data_center_id: int

        model = SampleModel(team_id=1, data_center_id=2)
        dumped = model.model_dump(by_alias=True)

        assert "teamId" in dumped
        assert "dataCenterId" in dumped
        assert dumped["teamId"] == 1
        assert dumped["dataCenterId"] == 2

    def test_model_validate_from_camel_case(self):
        class SampleModel(CamelModel):
            team_id: int
            is_private: bool

        model = SampleModel.model_validate({"teamId": 123, "isPrivate": True})

        assert model.team_id == 123
        assert model.is_private is True

    def test_model_validate_from_snake_case(self):
        class SampleModel(CamelModel):
            team_id: int
            is_private: bool

        model = SampleModel.model_validate({"team_id": 456, "is_private": False})

        assert model.team_id == 456
        assert model.is_private is False


class TestCamelModelExport:
    """Tests for CamelModel export methods."""

    def test_to_dict_default(self):
        """to_dict should export with camelCase keys by default."""

        class SampleModel(CamelModel):
            team_id: int
            user_name: str

        model = SampleModel(team_id=1, user_name="test")
        result = model.to_dict()

        assert result == {"teamId": 1, "userName": "test"}

    def test_to_dict_snake_case(self):
        """to_dict with by_alias=False should export with snake_case keys."""

        class SampleModel(CamelModel):
            team_id: int
            user_name: str

        model = SampleModel(team_id=1, user_name="test")
        result = model.to_dict(by_alias=False)

        assert result == {"team_id": 1, "user_name": "test"}

    def test_to_dict_exclude_none(self):
        """to_dict with exclude_none=True should omit None values."""

        class SampleModel(CamelModel):
            team_id: int
            optional_field: str | None = None

        model = SampleModel(team_id=1, optional_field=None)
        result = model.to_dict(exclude_none=True)

        assert result == {"teamId": 1}
        assert "optionalField" not in result

    def test_to_json_default(self):
        """to_json should export as JSON string with camelCase keys."""

        class SampleModel(CamelModel):
            team_id: int

        model = SampleModel(team_id=42)
        result = model.to_json()

        assert json.loads(result) == {"teamId": 42}

    def test_to_json_with_indent(self):
        """to_json with indent should format output."""

        class SampleModel(CamelModel):
            team_id: int

        model = SampleModel(team_id=42)
        result = model.to_json(indent=2)

        assert json.loads(result) == {"teamId": 42}
        assert "\n" in result

    def test_to_yaml_default(self):
        """to_yaml should export as YAML string with camelCase keys."""

        class SampleModel(CamelModel):
            team_id: int
            user_name: str

        model = SampleModel(team_id=1, user_name="test")
        result = model.to_yaml()

        assert "teamId: 1" in result
        assert "userName: test" in result

    def test_to_yaml_snake_case(self):
        """to_yaml with by_alias=False should use snake_case keys."""

        class SampleModel(CamelModel):
            team_id: int

        model = SampleModel(team_id=1)
        result = model.to_yaml(by_alias=False)

        assert "team_id: 1" in result


class TestResourceList:
    def test_create_with_list(self):
        """ResourceList should be created with a list of items."""

        class Item(BaseModel):
            id: int
            name: str

        items = [Item(id=1, name="first"), Item(id=2, name="second")]
        resource_list = ResourceList[Item](root=items)

        assert len(resource_list) == 2
        assert resource_list.root == items

    def test_iteration(self):
        """ResourceList should support iteration."""

        class Item(BaseModel):
            value: int

        items = [Item(value=i) for i in range(5)]
        resource_list = ResourceList[Item](root=items)

        iterated = list(resource_list)
        assert iterated == items

    def test_indexing(self):
        """ResourceList should support indexing."""

        class Item(BaseModel):
            id: int

        items = [Item(id=10), Item(id=20), Item(id=30)]
        resource_list = ResourceList[Item](root=items)

        assert resource_list[0].id == 10
        assert resource_list[1].id == 20
        assert resource_list[-1].id == 30

    def test_len(self):
        """ResourceList should support len()."""

        class Item(BaseModel):
            id: int

        resource_list = ResourceList[Item](root=[Item(id=i) for i in range(7)])
        assert len(resource_list) == 7

    def test_empty_list(self):
        """ResourceList should handle empty lists."""

        class Item(BaseModel):
            id: int

        resource_list = ResourceList[Item](root=[])
        assert len(resource_list) == 0
        assert list(resource_list) == []


class TestResourceListExport:
    """Tests for ResourceList export methods."""

    def test_to_list_default(self):
        """to_list should export items as list of dicts with camelCase keys."""

        class Item(CamelModel):
            item_id: int
            item_name: str

        items = [Item(item_id=1, item_name="a"), Item(item_id=2, item_name="b")]
        resource_list = ResourceList[Item](root=items)
        result = resource_list.to_list()

        assert result == [
            {"itemId": 1, "itemName": "a"},
            {"itemId": 2, "itemName": "b"},
        ]

    def test_to_list_snake_case(self):
        """to_list with by_alias=False should use snake_case keys."""

        class Item(CamelModel):
            item_id: int

        items = [Item(item_id=1)]
        resource_list = ResourceList[Item](root=items)
        result = resource_list.to_list(by_alias=False)

        assert result == [{"item_id": 1}]

    def test_to_json_default(self):
        """to_json should export as JSON array string."""

        class Item(CamelModel):
            item_id: int

        items = [Item(item_id=1), Item(item_id=2)]
        resource_list = ResourceList[Item](root=items)
        result = resource_list.to_json()

        assert json.loads(result) == [{"itemId": 1}, {"itemId": 2}]

    def test_to_json_with_indent(self):
        """to_json with indent should format output."""

        class Item(CamelModel):
            item_id: int

        items = [Item(item_id=1)]
        resource_list = ResourceList[Item](root=items)
        result = resource_list.to_json(indent=2)

        assert "\n" in result
        assert '"itemId": 1' in result

    def test_to_list_empty(self):
        """to_list should handle empty lists."""

        class Item(CamelModel):
            item_id: int

        resource_list = ResourceList[Item](root=[])
        result = resource_list.to_list()

        assert result == []

    def test_to_yaml_default(self):
        """to_yaml should export as YAML string."""

        class Item(CamelModel):
            item_id: int

        items = [Item(item_id=1), Item(item_id=2)]
        resource_list = ResourceList[Item](root=items)
        result = resource_list.to_yaml()

        assert "itemId: 1" in result
        assert "itemId: 2" in result


class TestResourceBase:
    def test_initialization_with_http_client(self):
        """ResourceBase should store the HTTP client."""
        mock_client = MagicMock()
        resource = ResourceBase(http_client=mock_client)

        assert resource._http_client is mock_client

    def test_inherits_from_api_operation_executor(self):
        """ResourceBase should inherit from _APIOperationExecutor."""
        from codesphere.core.handler import _APIOperationExecutor

        assert issubclass(ResourceBase, _APIOperationExecutor)
