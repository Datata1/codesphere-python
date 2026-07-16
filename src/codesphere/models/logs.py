from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import ConfigDict, Field

from ..core.models import CamelModel


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


# ---------------------------------------------------------------------------
# Stream targets (shared between the async and sync clients so isinstance
# checks work regardless of which client flavor created them).
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StageTarget:
    """Logs of a pipeline stage (prepare/test/run)."""

    stage: LogStage | str
    step: int = 0


@dataclass(frozen=True, slots=True)
class ServerTarget:
    """Run logs of a specific server in a Multi Server Deployment."""

    step: int
    server: str


@dataclass(frozen=True, slots=True)
class ReplicaTarget:
    """Run logs of a specific replica."""

    step: int
    replica: str


type LogTarget = StageTarget | ServerTarget | ReplicaTarget
