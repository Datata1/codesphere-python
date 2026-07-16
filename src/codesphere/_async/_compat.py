"""Async primitives whose sync counterpart is produced by name replacement.

unasyncd maps most constructs automatically (asyncio.sleep -> time.sleep,
async def/await, __aenter__ -> __enter__, ...). Anything it cannot map is
aliased here; the generated sync twin replaces ``asyncio`` with
``threading`` (see ``per_file_add_replacements`` in pyproject.toml).
"""

import asyncio

Lock = asyncio.Lock

__all__ = ["Lock"]
