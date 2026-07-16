"""Feature-flag engine: snapshot models, requirement declarations, cache.

This module lives at the top level (not in ``core``) on purpose:
``core.base`` imports ``http_client`` at module level, so ``http_client``
must not import from ``codesphere.core``. The engine only depends on
pydantic and :mod:`codesphere.exceptions`, which keeps the import graph
cycle-free. The public read API is :class:`codesphere.resources.flags.FlagsResource`.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict

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


def __getattr__(name: str) -> Any:
    # Backward compatibility: FlagsStore historically lived here. The
    # async implementation now lives in codesphere._async.flags_store.
    if name == "FlagsStore":
        from ._async.flags_store import FlagsStore

        return FlagsStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
