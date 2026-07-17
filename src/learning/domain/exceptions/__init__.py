"""
Learning Domain Exception Hierarchy — ADR-022 compliant.

Each error inherits from ``LearningDomainError → DomainError → FoundationError``
for full hierarchy compatibility AND from ``ValueError`` for backward
compatibility.

Usage::

    from learning.domain.exceptions import LearningDomainError

    raise LearningDomainError("Feedback reason is required for rejected decisions")
"""
from __future__ import annotations

from foundation import DomainError


class LearningDomainError(DomainError, ValueError):
    """Base error for all Learning BC domain exceptions.

    Inherits from both ``DomainError`` (for domain hierarchy) and
    ``ValueError`` (for backward compatibility with existing code that
    catches ``ValueError`` directly).
    """

    code = "LEARNING_ERROR"

    def __str__(self) -> str:
        return self.message or self.detail


__all__ = [
    "LearningDomainError",
]
