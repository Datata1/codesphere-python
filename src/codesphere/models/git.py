from __future__ import annotations

from ..core.models import CamelModel


class GitHead(CamelModel):
    head: str
