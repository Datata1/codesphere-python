from __future__ import annotations

from enum import Enum
from typing import Optional

from ....core.base import CamelModel


class LogStage(str, Enum):
    PREPARE = "prepare"
    TEST = "test"
    RUN = "run"


class LogEntry(CamelModel):
    model_config = {"extra": "allow"}

    timestamp: Optional[str] = None
    kind: Optional[str] = None  # "I" for info, "E" for error
    data: Optional[str] = None  # The actual log content

    def get_text(self) -> str:
        return self.data or ""


class LogProblem(CamelModel):
    status: int
    reason: str
    detail: Optional[str] = None
