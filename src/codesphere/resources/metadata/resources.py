from pydantic import Field

from ...core import AsyncCallable, ResourceBase
from ...core.base import ResourceList
from .operations import _LIST_DC_OP, _LIST_IMAGES_OP, _LIST_PLANS_OP
from .schemas import Datacenter, Image, WsPlan


class MetadataResource(ResourceBase):
    list_datacenters_op: AsyncCallable[ResourceList[Datacenter]] = Field(
        default=_LIST_DC_OP, exclude=True
    )
    list_plans_op: AsyncCallable[ResourceList[WsPlan]] = Field(
        default=_LIST_PLANS_OP, exclude=True
    )
    list_images_op: AsyncCallable[ResourceList[Image]] = Field(
        default=_LIST_IMAGES_OP, exclude=True
    )

    async def list_datacenters(self) -> list[Datacenter]:
        result = await self.list_datacenters_op()
        return result.root

    async def list_plans(self) -> list[WsPlan]:
        result = await self.list_plans_op()
        return result.root

    async def list_images(self) -> list[Image]:
        result = await self.list_images_op()
        return result.root
