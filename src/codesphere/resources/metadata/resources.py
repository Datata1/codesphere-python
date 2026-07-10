from ...core import ResourceBase
from .operations import _LIST_DC_OP, _LIST_IMAGES_OP, _LIST_PLANS_OP
from .schemas import Datacenter, Image, WsPlan


class MetadataResource(ResourceBase):
    async def list_datacenters(self) -> list[Datacenter]:
        result = await self._execute(_LIST_DC_OP)
        return result.root

    async def list_plans(self) -> list[WsPlan]:
        result = await self._execute(_LIST_PLANS_OP)
        return result.root

    async def list_images(self) -> list[Image]:
        result = await self._execute(_LIST_IMAGES_OP)
        return result.root
