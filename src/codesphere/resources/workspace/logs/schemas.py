from __future__ import annotations

from enum import Enum

from pydantic import ConfigDict, Field

from ....core.base import CamelModel


class LogStage(str, Enum):
    PREPARE = "prepare"
    TEST = "test"
    RUN = "run"


class LogKind(str, Enum):
    INFO = "I"
    ERROR = "E"


class LogEntry(CamelModel):
    model_config = ConfigDict(extra="allow")

    timestamp: str | None = None
    # Known kinds are typed; unknown values fall back to the raw string.
    kind: LogKind | str | None = Field(default=None, union_mode="left_to_right")
    data: str | None = None  # The actual log content

    def get_text(self) -> str:
        return self.data or ""


class LogProblem(CamelModel):
    status: int
    reason: str
    detail: str | None = None
