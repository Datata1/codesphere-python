from __future__ import annotations
from pydantic import BaseModel
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Datacenters(BaseModel):
    """Defines the request body for creating a team."""

    id: int
    name: str
    city: str
    countryCode: str


class Characteristics(BaseModel):
    """Defines the hardware and service characteristics of a workspace plan."""

    id: int
    CPU: float
    GPU: int
    RAM: int
    SSD: int
    TempStorage: int
    onDemand: bool


class WsPlans(BaseModel):
    """Contains all fields that appear in a workspace-plans response."""

    id: int
    priceUsd: int
    title: str
    deprecated: bool
    characteristics: Characteristics
    maxReplicas: int


class Images(BaseModel):
    """Represents a team as it appears in the list response."""

    id: str
    name: str
    supportedUntil: datetime.datetime
