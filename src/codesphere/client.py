"""Compatibility shim; the client lives in codesphere._async.client."""

from ._async.client import CodesphereSDK

__all__ = ["CodesphereSDK"]
