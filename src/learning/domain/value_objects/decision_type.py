"""
DecisionType Value Object — Classifies the type of human/AI decision.

Enum values represent the full spectrum of decision outcomes in the Learning BC.
"""
from __future__ import annotations

from enum import Enum


class DecisionType(str, Enum):
    """Classification of a human/AI decision on content.

    Attributes:
        APPROVED: Human explicitly approved the content.
        REJECTED: Human explicitly rejected the content.
        AUTO_APPROVED: System auto-approved based on confidence thresholds.
        AUTO_REJECTED: System auto-rejected based on confidence thresholds.
        OVERRIDDEN: Human overrode a previous auto-decision.
    """

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTO_APPROVED = "AUTO_APPROVED"
    AUTO_REJECTED = "AUTO_REJECTED"
    OVERRIDDEN = "OVERRIDDEN"

    @property
    def is_rejection(self) -> bool:
        """True if this decision type represents a rejection."""
        return self in (
            DecisionType.REJECTED,
            DecisionType.AUTO_REJECTED,
        )

    @property
    def is_approval(self) -> bool:
        """True if this decision type represents an approval."""
        return self in (
            DecisionType.APPROVED,
            DecisionType.AUTO_APPROVED,
        )

    @property
    def is_auto(self) -> bool:
        """True if this decision was made by the system (not human)."""
        return self in (
            DecisionType.AUTO_APPROVED,
            DecisionType.AUTO_REJECTED,
        )
