"""
Sync→Async Bridge — TEMPORAL utility for calling sync services from async handlers.

All Application Services are synchronous (they use sync SQLAlchemy sessions).
FastAPI handlers are ``async def``. This bridge wraps sync calls using
``run_in_executor`` to avoid blocking the event loop.

.. warning::
    This module is TEMPORAL. It will be REMOVED when the Application Layer
    becomes natively async (planned for a future sprint).

Usage::

    from ingestion.presentation.bridge import run_sync

    async def register_source_handler(cmd, service):
        result = await run_sync(service.execute_register_source, cmd)
        return result
"""

from __future__ import annotations

import asyncio
from typing import Callable, TypeVar

T = TypeVar("T")


# TEMPORAL: sync→async bridge — DELETE when Application Layer becomes async
async def run_sync(func: Callable[..., T], *args: object) -> T:
    """Execute a sync function in the thread pool.

    Wraps ``asyncio.get_event_loop().run_in_executor(None, func, *args)``
    to run synchronous Application Service calls without blocking the
    event loop.

    Args:
        func: The synchronous callable to execute.
        *args: Arguments to pass to the function.

    Returns:
        The return value of the function.

    Example::

        result = await run_sync(service.execute_register_source, cmd)
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
