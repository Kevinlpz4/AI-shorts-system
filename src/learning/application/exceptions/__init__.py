"""
Application Layer Exception Hierarchy — ADR-022 compliant.

Exporta ApplicationErrorCode, CommandValidationError, ResourceNotFoundError.

Uso::

    from learning.application.exceptions import (
        ApplicationErrorCode,
        CommandValidationError,
        ResourceNotFoundError,
    )
"""

from __future__ import annotations

from learning.application.exceptions.application_error import (
    CommandValidationError,
    ResourceNotFoundError,
)
from learning.application.exceptions.error_code import ApplicationErrorCode

__all__ = [
    "ApplicationErrorCode",
    "CommandValidationError",
    "ResourceNotFoundError",
]
