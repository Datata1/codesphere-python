from __future__ import annotations

from enum import Enum

from pydantic import ConfigDict

from ....core.base import CamelModel


class LogStage(str, Enum):
    PREPARE = "prepare"
    TEST = "test"
    RUN = "run"


class LogEntry(CamelModel):
    model_config = ConfigDict(extra="allow")

    timestamp: str | None = None
    kind: str | None = None  # "I" for info, "E" for error
    data: str | None = None  # The actual log content

    def get_text(self) -> str:
        return self.data or ""


class LogProblem(CamelModel):
    status: int
    reason: str
    detail: str | None = None
