"""
Source definition contracts for the Runtime layer.

Re-exported from ``__init__.py`` for backward compatibility.
"""
from __future__ import annotations

from runtime.contracts import (
    AuthConfig,
    RateLimitConfig,
    RetryPolicy,
    SourceDefinition,
)

__all__ = ["AuthConfig", "RateLimitConfig", "RetryPolicy", "SourceDefinition"]
