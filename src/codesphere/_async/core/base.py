from collections.abc import Mapping
from typing import Any, ClassVar, TypeVar

import httpx
from pydantic import PrivateAttr

from codesphere.core.models import CamelModel
from codesphere.core.models import ResourceList as ResourceList
from codesphere.core.operations import APIOperation
from codesphere.exceptions import StaleModelError
from codesphere.feature_flags import FlagRequirement

from ..http_client import APIHttpClient
from .handler import RequestData, execute_operation

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
        timeout: httpx.Timeout | float | None = None,
        **path_params: Any,
    ) -> ResponseT:
        return await execute_operation(
            self._http_client,
            op,
            data=data,
            params=params,
            path_params=path_params,
            timeout=timeout,
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


class BoundModel(CamelModel):
    """API entity that carries the HTTP client it was fetched with.

    Instances returned by the SDK get their client attached automatically,
    which lets entity methods (e.g. ``workspace.delete()``) make further
    API calls.

    A write that the SDK cannot verify marks the instance **stale**: its
    field values are dropped and reads raise
    :class:`~codesphere.StaleModelError` until ``refresh()`` re-reads the
    entity. Identity fields survive, so the instance can still be logged
    and re-fetched. See :meth:`_mark_stale`.
    """

    #: Fields that stay readable on a stale instance. An entity's identity
    #: cannot be changed by a write, so it is always safe to report.
    _identity_fields: ClassVar[tuple[str, ...]] = ("id",)

    _http_client: APIHttpClient | None = PrivateAttr(default=None)
    _stale: bool = PrivateAttr(default=False)

    def __getattr__(self, item: str) -> Any:
        # Pydantic keeps field values in __dict__, so this only runs once a
        # lookup has already failed: zero cost until a model goes stale.
        if self._is_stale() and item in type(self).__pydantic_fields__:
            raise StaleModelError(type(self).__name__, item)
        # Delegate to pydantic, which resolves private attributes here.
        # It defines __getattr__ only at runtime, so it is fetched
        # dynamically rather than called through super() directly.
        parent = getattr(super(), "__getattr__", None)
        if parent is None:  # pragma: no cover - pydantic always defines it
            raise AttributeError(item)
        return parent(item)

    def _is_stale(self) -> bool:
        private = object.__getattribute__(self, "__pydantic_private__")
        return bool(private and private.get("_stale"))

    def _mark_stale(self) -> None:
        """Drop local field values the SDK can no longer vouch for.

        Called after a write whose resulting server state is unknown.
        Clearing ``__dict__`` (rather than setting a flag beside intact
        values) is what routes later reads through ``__getattr__``.
        """
        identity = {
            name: value
            for name, value in self.__dict__.items()
            if name in type(self)._identity_fields
        }
        # Also drops cached_property managers; they rebuild after refresh.
        self.__dict__.clear()
        self.__dict__.update(identity)
        self._stale = True

    def _adopt(self, fresh: "BoundModel") -> None:
        """Repopulate from a server-authoritative re-read."""
        self.__dict__.clear()
        self.__dict__.update(fresh.__dict__)
        self._stale = False

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        # Pydantic serializes straight from __dict__, so without this a
        # stale model would quietly dump only its identity fields.
        if self._is_stale():
            raise StaleModelError(type(self).__name__)
        return super().model_dump(*args, **kwargs)

    def model_dump_json(self, *args: Any, **kwargs: Any) -> str:
        if self._is_stale():
            raise StaleModelError(type(self).__name__)
        return super().model_dump_json(*args, **kwargs)

    def __repr_args__(self) -> Any:
        # Keep repr() working for debugging, but say why it looks empty.
        if self._is_stale():
            return [*super().__repr_args__(), ("stale", True)]
        return super().__repr_args__()

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
        timeout: httpx.Timeout | float | None = None,
        **path_params: Any,
    ) -> ResponseT:
        return await execute_operation(
            self._client(),
            op,
            data=data,
            params=params,
            path_params=path_params,
            timeout=timeout,
        )

    async def _require_flag(self, requirement: FlagRequirement) -> None:
        """Fail fast unless the platform flag is enabled (non-operation paths)."""
        await self._client().flags_store.require(requirement)
