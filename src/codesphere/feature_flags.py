"""Feature-flag engine: snapshot models, requirement declarations, cache.

This module lives at the top level (not in ``core``) on purpose:
``core.base`` imports ``http_client`` at module level, so ``http_client``
must not import from ``codesphere.core``. The engine only depends on
pydantic and :mod:`codesphere.exceptions`, which keeps the import graph
cycle-free. The public read API is :class:`codesphere.resources.flags.FlagsResource`.
"""

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from .exceptions import (
    FeatureNotAvailableError,
    FeatureNotEnabledError,
    NotFoundError,
)

if TYPE_CHECKING:
    from .http_client import APIHttpClient

FLAGS_ENDPOINT = "/ide-service/flags"


class FlagCategory(StrEnum):
    INTERNAL = "internal"
    PREVIEW = "preview"
    FEATURES = "features"


class CategoryFlags(BaseModel):
    """Available and enabled flags of one category."""

    model_config = ConfigDict(frozen=True)

    available: frozenset[str] = frozenset()
    enabled: frozenset[str] = frozenset()


class FlagsSnapshot(BaseModel):
    """Immutable view of the platform's feature flags at fetch time."""

    model_config = ConfigDict(frozen=True)

    internal: CategoryFlags = CategoryFlags()
    preview: CategoryFlags = CategoryFlags()
    features: CategoryFlags = CategoryFlags()

    @classmethod
    def empty(cls) -> "FlagsSnapshot":
        return cls()

    def category(self, category: FlagCategory) -> CategoryFlags:
        match category:
            case FlagCategory.INTERNAL:
                return self.internal
            case FlagCategory.PREVIEW:
                return self.preview
            case FlagCategory.FEATURES:
                return self.features

    def is_available(self, flag: str, category: FlagCategory | None = None) -> bool:
        """Whether ``flag`` exists on this instance (in any or one category)."""
        if category is not None:
            return flag in self.category(category).available
        return any(flag in self.category(c).available for c in FlagCategory)

    def is_enabled(self, flag: str, category: FlagCategory | None = None) -> bool:
        """Whether ``flag`` is enabled on this instance (in any or one category)."""
        if category is not None:
            return flag in self.category(category).enabled
        return any(flag in self.category(c).enabled for c in FlagCategory)

    def categories_with(self, flag: str) -> tuple[FlagCategory, ...]:
        """All categories in which ``flag`` is available (collision insight)."""
        return tuple(c for c in FlagCategory if flag in self.category(c).available)


@dataclass(frozen=True, slots=True)
class FlagRequirement:
    """Declares that an SDK feature needs a platform flag to be enabled.

    Attach to an :class:`~codesphere.core.operations.APIOperation` via
    ``required_flag=...`` (enforced automatically before any request), or
    check explicitly with ``await self._require_flag(...)``. SDK-internal
    declarations should always set an explicit ``category``.
    """

    flag: str
    category: FlagCategory | None = None


class FlagsStore:
    """Per-client cache of the platform's feature flags.

    Fetches ``GET /ide-service/flags`` lazily on first need (under a lock,
    so concurrent gated calls trigger one request), then caches for the
    client's lifetime. A 404 — the instance predates feature flags — is
    cached as an empty snapshot: reads report nothing available and gated
    calls fail closed. Transient errors propagate uncached.
    """

    def __init__(self, client: "APIHttpClient") -> None:
        self._client = client
        self._snapshot: FlagsSnapshot | None = None
        self._legacy_platform = False
        self._lock = asyncio.Lock()

    async def get(self, *, refresh: bool = False) -> FlagsSnapshot:
        async with self._lock:
            if self._snapshot is None or refresh:
                self._snapshot = await self._fetch()
            return self._snapshot

    async def _fetch(self) -> FlagsSnapshot:
        try:
            response = await self._client.request("GET", FLAGS_ENDPOINT)
        except NotFoundError:
            self._legacy_platform = True
            return FlagsSnapshot.empty()
        self._legacy_platform = False
        return FlagsSnapshot.model_validate(response.json())

    async def require(self, requirement: FlagRequirement) -> None:
        """Raise unless the required flag is enabled on this instance."""
        snapshot = await self.get()
        flag, category = requirement.flag, requirement.category
        category_str = str(category) if category is not None else None

        if not snapshot.is_available(flag, category):
            raise FeatureNotAvailableError(
                flag=flag,
                category=category_str,
                legacy_platform=self._legacy_platform,
            )
        if not snapshot.is_enabled(flag, category):
            raise FeatureNotEnabledError(flag=flag, category=category_str)

    def cached(self) -> FlagsSnapshot | None:
        """The current snapshot, or None if nothing has been fetched yet."""
        return self._snapshot

    def invalidate(self) -> None:
        """Drop the cached snapshot; the next need re-fetches."""
        self._snapshot = None
