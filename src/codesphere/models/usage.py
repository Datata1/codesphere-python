from __future__ import annotations

from datetime import datetime
from enum import Enum

from ..core.models import CamelModel


class ServiceAction(str, Enum):
    START = "start"
    STOP = "stop"


class LandscapeServiceSummary(CamelModel):
    resource_id: str
    resource_name: str
    usage_seconds: float
    plan_name: str
    always_on: bool
    replicas: int
    type: str


class LandscapeServiceEvent(CamelModel):
    id: int
    initiator_id: str
    initiator_email: str
    resource_id: str
    date: datetime
    action: ServiceAction
    always_on: bool
    replicas: int
    service_name: str
