from typing import Any, Generic, List, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, RootModel
from pydantic.alias_generators import to_camel

from ..http_client import APIHttpClient
from .handler import _APIOperationExecutor

ModelT = TypeVar("ModelT", bound=BaseModel)


class ResourceBase(_APIOperationExecutor):
    def __init__(self, http_client: APIHttpClient):
        self._http_client = http_client


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )

    def to_dict(
        self, *, by_alias: bool = True, exclude_none: bool = False
    ) -> dict[str, Any]:
        """Export model as a Python dictionary.

        Args:
            by_alias: Use camelCase keys (API format) if True, snake_case if False.
            exclude_none: Exclude fields with None values if True.

        Returns:
            Dictionary representation of the model.
        """
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none)

    def to_json(
        self,
        *,
        by_alias: bool = True,
        exclude_none: bool = False,
        indent: int | None = None,
    ) -> str:
        """Export model as a JSON string.

        Args:
            by_alias: Use camelCase keys (API format) if True, snake_case if False.
            exclude_none: Exclude fields with None values if True.
            indent: Number of spaces for indentation. None for compact output.

        Returns:
            JSON string representation of the model.
        """
        return self.model_dump_json(
            by_alias=by_alias, exclude_none=exclude_none, indent=indent
        )

    def to_yaml(self, *, by_alias: bool = True, exclude_none: bool = False) -> str:
        """Export model as a YAML string.

        Args:
            by_alias: Use camelCase keys (API format) if True, snake_case if False.
            exclude_none: Exclude fields with None values if True.

        Returns:
            YAML string representation of the model.
        """
        data = self.to_dict(by_alias=by_alias, exclude_none=exclude_none)
        return yaml.dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


class ResourceList(RootModel[List[ModelT]], Generic[ModelT]):
    root: List[ModelT]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)

    def to_list(
        self, *, by_alias: bool = True, exclude_none: bool = False
    ) -> list[dict[str, Any]]:
        """Export all items as a list of dictionaries.

        Args:
            by_alias: Use camelCase keys (API format) if True, snake_case if False.
            exclude_none: Exclude fields with None values if True.

        Returns:
            List of dictionary representations.
        """
        return [
            item.model_dump(by_alias=by_alias, exclude_none=exclude_none)
            for item in self.root
        ]

    def to_json(
        self,
        *,
        by_alias: bool = True,
        exclude_none: bool = False,
        indent: int | None = None,
    ) -> str:
        """Export all items as a JSON array string.

        Args:
            by_alias: Use camelCase keys (API format) if True, snake_case if False.
            exclude_none: Exclude fields with None values if True.
            indent: Number of spaces for indentation. None for compact output.

        Returns:
            JSON array string representation.
        """
        import json

        return json.dumps(
            self.to_list(by_alias=by_alias, exclude_none=exclude_none), indent=indent
        )

    def to_yaml(self, *, by_alias: bool = True, exclude_none: bool = False) -> str:
        """Export all items as a YAML string.

        Args:
            by_alias: Use camelCase keys (API format) if True, snake_case if False.
            exclude_none: Exclude fields with None values if True.

        Returns:
            YAML string representation.
        """
        return yaml.dump(
            self.to_list(by_alias=by_alias, exclude_none=exclude_none),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
