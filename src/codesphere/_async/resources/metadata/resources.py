import httpx

from ...core import ResourceBase
from .operations import _LIST_DC_OP, _LIST_IMAGES_OP, _LIST_PLANS_OP
from .schemas import Datacenter, Image, WsPlan


class MetadataResource(ResourceBase):
    async def list_datacenters(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> list[Datacenter]:
        result = await self._execute(_LIST_DC_OP, timeout=timeout)
        return result.root

    async def list_plans(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> list[WsPlan]:
        result = await self._execute(_LIST_PLANS_OP, timeout=timeout)
        return result.root

    async def list_images(
        self, *, timeout: httpx.Timeout | float | None = None
    ) -> list[Image]:
        result = await self._execute(_LIST_IMAGES_OP, timeout=timeout)
        return result.root
