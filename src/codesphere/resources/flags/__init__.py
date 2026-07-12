"""Feature flags of the connected Codesphere instance (``sdk.flags``).

This package deviates from the canonical resource layout in one way:
there is no ``operations.py``. The fetch lives in
:class:`codesphere.feature_flags.FlagsStore` so that ``sdk.flags`` and
operation gating (``APIOperation.required_flag``) share a single cache.
"""

from .resources import FlagsResource
from .schemas import CategoryFlags, FlagCategory, FlagsSnapshot

__all__ = [
    "CategoryFlags",
    "FlagCategory",
    "FlagsResource",
    "FlagsSnapshot",
]
