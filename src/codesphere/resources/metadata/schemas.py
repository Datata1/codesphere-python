from __future__ import annotations
import datetime

from pydantic import Field

from ...core.base import CamelModel


class Datacenter(CamelModel):
    """Represents a physical data center location."""

    id: int
    name: str
    city: str
    country_code: str


class Characteristic(CamelModel):
    """Defines the resource specifications for a WsPlan."""

    id: int
    cpu: float = Field(validation_alias="CPU")
    gpu: int = Field(validation_alias="GPU")
    ram: int = Field(validation_alias="RAM")
    ssd: int = Field(validation_alias="SSD")
    temp_storage: int = Field(validation_alias="TempStorage")
    on_demand: bool


class WsPlan(CamelModel):
    """
    Represents a purchasable workspace plan.
    """

    id: int
    price_usd: int
    title: str
    deprecated: bool
    characteristics: Characteristic
    max_replicas: int


class Image(CamelModel):
    """Represents a runnable workspace base image."""

    id: str
    name: str
    supported_until: datetime.datetime
