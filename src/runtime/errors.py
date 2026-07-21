"""
Runtime Error Codes and RuntimeError exception.

This module defines ``RuntimeErrorCode`` (str, Enum) for machine-readable
error classification, and ``RuntimeError`` for operational exceptions
within the Runtime orchestration layer.

Usage::

    from runtime.errors import RuntimeErrorCode, RuntimeError

    raise RuntimeError(
        code=RuntimeErrorCode.SOURCE_FETCH_FAILED,
        message="Failed to fetch from RSS source",
        detail="Connection timeout",
    )
"""
from __future__ import annotations

from enum import Enum


class RuntimeErrorCode(str, Enum):
    """Runtime error codes — machine-readable classification.

    Each code represents a distinct failure mode in the Runtime layer.
    ``str, Enum`` allows direct use in Result[Error] and string formatting.
    """

    SOURCE_FETCH_FAILED = "SOURCE_FETCH_FAILED"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    STEP_EXECUTION_FAILED = "STEP_EXECUTION_FAILED"
    JOB_EXECUTION_FAILED = "JOB_EXECUTION_FAILED"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    PIPELINE_FAILED = "PIPELINE_FAILED"
    ADAPTER_NOT_FOUND = "ADAPTER_NOT_FOUND"
    REGISTRY_ERROR = "REGISTRY_ERROR"


class RuntimeError(Exception):
    """Runtime operational exception.

    Represents a failure in the Runtime orchestration layer. NOT a domain
    error — domain errors stay in their BCs. RuntimeError is for cross-BC
    coordination failures.

    Attributes:
        code: Machine-readable error code.
        message: Human-readable description of what went wrong.
        detail: Optional additional context (timeout, stack trace summary, etc.).
    """

    def __init__(
        self,
        code: RuntimeErrorCode,
        message: str,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail

    def __str__(self) -> str:
        """Formats as ``[CODE] message`` or ``[CODE] message: detail``."""
        if self.detail:
            return f"[{self.code.value}] {self.message}: {self.detail}"
        return f"[{self.code.value}] {self.message}"
