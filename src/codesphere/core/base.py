from collections.abc import Mapping
from typing import Any, Generic, Literal, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, PrivateAttr, RootModel
from pydantic.alias_generators import to_camel

from ..feature_flags import FlagRequirement
from ..http_client import APIHttpClient
from .handler import RequestData, execute_operation
from .operations import APIOperation

ModelT = TypeVar("ModelT", bound=BaseModel)
ResponseT = TypeVar("ResponseT")


class ResourceBase:
    """Base for resource and manager classes bound to an HTTP client."""

    def __init__(self, http_client: APIHttpClient):
        self._http_client = http_client

    async def _execute(
        self,
        op: APIOperation[ResponseT],
        *,
        data: RequestData | None = None,
        params: Mapping[str, Any] | None = None,
        **path_params: Any,
    ) -> ResponseT:
        return await execute_operation(
            self._http_client, op, data=data, params=params, path_params=path_params
        )

    async def _require_flag(self, requirement: FlagRequirement) -> None:
        """Fail fast unless the platform flag is enabled (non-operation paths)."""
        await self._http_client.flags_store.require(requirement)


class TeamScopedResource(ResourceBase):
    """Base for managers operating within one team."""

    def __init__(self, http_client: APIHttpClient, team_id: int):
        super().__init__(http_client)
        self.team_id = team_id


class WorkspaceScopedResource(ResourceBase):
    """Base for managers operating within one workspace."""

    def __init__(self, http_client: APIHttpClient, workspace_id: int):
        super().__init__(http_client)
        self.workspace_id = workspace_id


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
        data = self.model_dump(
            by_alias=by_alias, exclude_none=exclude_none, mode="json"
        )
        return yaml.safe_dump(
            data, default_flow_style=False, allow_unicode=True, sort_keys=False
        )


class BoundModel(CamelModel):
    """API entity that carries the HTTP client it was fetched with.

    Instances returned by the SDK get their client attached automatically,
    which lets entity methods (e.g. ``workspace.delete()``) make further
    API calls.
    """

    _http_client: APIHttpClient | None = PrivateAttr(default=None)

    def _client(self) -> APIHttpClient:
        if self._http_client is None or not hasattr(self._http_client, "request"):
            raise RuntimeError(
                "Cannot access resource on a detached model. HTTP client missing."
            )
        return self._http_client

    async def _execute(
        self,
        op: APIOperation[ResponseT],
        *,
        data: RequestData | None = None,
        params: Mapping[str, Any] | None = None,
        **path_params: Any,
    ) -> ResponseT:
        return await execute_operation(
            self._client(), op, data=data, params=params, path_params=path_params
        )

    async def _require_flag(self, requirement: FlagRequirement) -> None:
        """Fail fast unless the platform flag is enabled (non-operation paths)."""
        await self._client().flags_store.require(requirement)


class ResourceList(RootModel[list[ModelT]], Generic[ModelT]):
    root: list[ModelT]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]

    def __len__(self):
        return len(self.root)

    def to_list(
        self,
        *,
        by_alias: bool = True,
        exclude_none: bool = False,
        mode: Literal["python", "json"] = "python",
    ) -> list[dict[str, Any]]:
        """Export all items as a list of dictionaries.

        Args:
            by_alias: Use camelCase keys (API format) if True, snake_case if False.
            exclude_none: Exclude fields with None values if True.
            mode: Serialization mode. "python" returns native Python objects,
                  "json" returns JSON-compatible types (e.g., datetime as ISO string).

        Returns:
            List of dictionary representations.
        """
        return [
            item.model_dump(by_alias=by_alias, exclude_none=exclude_none, mode=mode)
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
            self.to_list(by_alias=by_alias, exclude_none=exclude_none, mode="json"),
            indent=indent,
        )

    def to_yaml(self, *, by_alias: bool = True, exclude_none: bool = False) -> str:
        """Export all items as a YAML string.

        Args:
            by_alias: Use camelCase keys (API format) if True, snake_case if False.
            exclude_none: Exclude fields with None values if True.

        Returns:
            YAML string representation.
        """
        return yaml.safe_dump(
            self.to_list(by_alias=by_alias, exclude_none=exclude_none, mode="json"),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
