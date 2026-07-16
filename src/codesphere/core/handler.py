"""Compatibility shim; the executor lives in codesphere._async.core.handler."""

from .._async.core.handler import (
    RequestData,
    _bind_client,
    execute_operation,
)

__all__ = ["RequestData", "_bind_client", "execute_operation"]
