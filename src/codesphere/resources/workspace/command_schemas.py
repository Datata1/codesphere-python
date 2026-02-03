"""
Input/Output schemas for workspace operations.

These are separated from the main schemas to avoid circular imports
between schemas.py and operations.py.
"""

from typing import Dict, Optional

from ...core.base import CamelModel


class CommandInput(CamelModel):
    """Input model for command execution."""

    command: str
    env: Optional[Dict[str, str]] = None


class CommandOutput(CamelModel):
    """Output model for command execution."""

    command: str
    working_dir: str
    output: str
    error: str


class WorkspaceStatus(CamelModel):
    """Status information for a workspace."""

    is_running: bool
