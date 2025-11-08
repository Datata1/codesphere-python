from __future__ import annotations
from pydantic import BaseModel
import datetime


class Datacenter(BaseModel):
    """Represents a physical data center location."""

    id: int
    name: str
    city: str
    countryCode: str


class Characteristic(BaseModel):
    """Defines the resource specifications for a WsPlan."""

    id: int
    CPU: float
    GPU: int
    RAM: int
    SSD: int
    TempStorage: int
    onDemand: bool


class WsPlan(BaseModel):
    """
    Represents a purchasable workspace plan.
    """

    id: int
    priceUsd: int
    title: str
    deprecated: bool
    characteristics: Characteristic
    maxReplicas: int


class Image(BaseModel):
    """Represents a runnable workspace base image."""

    id: str
    name: str
    supportedUntil: datetime.datetime
