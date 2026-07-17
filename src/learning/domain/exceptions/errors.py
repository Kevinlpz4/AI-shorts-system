"""
Learning Error Codes — ADR-022 compliant.

Each Bounded Context defines its own ``str, Enum`` independent of Foundation's
``ErrorCode``. This follows ADR-022 which specifies that ErrorCodes are NOT
extensible by inheritance (Python 3.11+ forbids subclassing Enums with members).

Usage::

    from learning.domain.exceptions.errors import LearningErrorCode

    error = Error(code=LearningErrorCode.FEEDBACK_NOT_FOUND, message="...")
"""
from __future__ import annotations

from enum import Enum


class LearningErrorCode(str, Enum):
    """Error codes for the Learning Bounded Context.

    Each code represents a well-known failure scenario in the domain.
    Used with ``Result.failure(Error(code=..., message=...))`` in repository
    ports and application services.
    """

    FEEDBACK_NOT_FOUND = "FEEDBACK_NOT_FOUND"
    SIGNAL_NOT_FOUND = "SIGNAL_NOT_FOUND"
    SOURCE_QUALITY_NOT_FOUND = "SOURCE_QUALITY_NOT_FOUND"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    DUPLICATE_FEEDBACK = "DUPLICATE_FEEDBACK"
    INVALID_DECISION_TYPE = "INVALID_DECISION_TYPE"
    INVALID_CONFIDENCE = "INVALID_CONFIDENCE"
    INVALID_WEIGHTS = "INVALID_WEIGHTS"
    WINDOW_INVALID = "WINDOW_INVALID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SIGNAL_ALREADY_FINALIZED = "SIGNAL_ALREADY_FINALIZED"
