from typing import List
from pydantic import Field
from ...core.base import ResourceList
from ...core import AsyncCallable
from ...core import ResourceBase
from .operations import _LIST_DC_OP, _LIST_IMAGES_OP, _LIST_PLANS_OP
from .schemas import Datacenter, WsPlan, Image


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

    async def list_datacenters(self) -> List[Datacenter]:
        result = await self.list_datacenters_op()
        return result.root

    async def list_plans(self) -> List[WsPlan]:
        result = await self.list_plans_op()
        return result.root

    async def list_images(self) -> List[Image]:
        result = await self.list_images_op()
        return result.root
