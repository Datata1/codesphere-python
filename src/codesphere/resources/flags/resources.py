from ...core import ResourceBase
from ...feature_flags import FlagCategory, FlagRequirement, FlagsSnapshot


class FlagsResource(ResourceBase):
    """Read the feature flags of the connected Codesphere instance.

    The snapshot is fetched lazily and cached for the client's lifetime;
    :meth:`refresh` re-fetches. The same cache backs operation gating, so
    a refresh here also affects gated SDK features.
    """

    async def get(self, *, refresh: bool = False) -> FlagsSnapshot:
        """The instance's flags snapshot (cached after the first call)."""
        return await self._http_client.flags_store.get(refresh=refresh)

    async def refresh(self) -> FlagsSnapshot:
        """Re-fetch the flags from the platform."""
        return await self.get(refresh=True)

    async def is_available(
        self, flag: str, category: FlagCategory | None = None
    ) -> bool:
        """Whether ``flag`` exists on this instance (any or one category)."""
        snapshot = await self.get()
        return snapshot.is_available(flag, category)

    async def is_enabled(self, flag: str, category: FlagCategory | None = None) -> bool:
        """Whether ``flag`` is enabled on this instance (any or one category)."""
        snapshot = await self.get()
        return snapshot.is_enabled(flag, category)

    async def require(self, flag: str, category: FlagCategory | None = None) -> None:
        """Raise :class:`~codesphere.FeatureFlagError` unless ``flag`` is enabled."""
        await self._http_client.flags_store.require(
            FlagRequirement(flag=flag, category=category)
        )
