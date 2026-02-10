from __future__ import annotations

from enum import Enum
from typing import Optional

from ....core.base import CamelModel


class LogStage(str, Enum):
    """Pipeline stage for log retrieval."""

    PREPARE = "prepare"
    TEST = "test"
    RUN = "run"


class LogEntry(CamelModel):
    """A single log entry from the workspace logs stream."""

    model_config = {"extra": "allow"}

    timestamp: Optional[str] = None
    kind: Optional[str] = None  # "I" for info, "E" for error, etc.
    data: Optional[str] = None  # The actual log content

    def get_text(self) -> str:
        """Get the log text."""
        return self.data or ""


class LogProblem(CamelModel):
    """Problem event from the logs SSE stream."""

    status: int
    reason: str
    detail: Optional[str] = None
