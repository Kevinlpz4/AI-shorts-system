"""
Application Layer Exception Hierarchy — ADR-022 compliant.

Exporta ApplicationErrorCode, CommandValidationError, ResourceNotFoundError.

Uso::

    from ingestion.application.exceptions import (
        ApplicationErrorCode,
        CommandValidationError,
        ResourceNotFoundError,
    )
"""

from __future__ import annotations

from ingestion.application.exceptions.application_error import (
    CommandValidationError,
    ResourceNotFoundError,
)
from ingestion.application.exceptions.error_code import ApplicationErrorCode

__all__ = [
    "ApplicationErrorCode",
    "CommandValidationError",
    "ResourceNotFoundError",
]
