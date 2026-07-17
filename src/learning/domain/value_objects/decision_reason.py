"""
DecisionReason Value Object — Classified reason for rejection/override decisions.

Every rejection or override MUST have a reason. Approvals may optionally have one.
"""
from __future__ import annotations

from enum import Enum


class DecisionReason(str, Enum):
    """Classified reason for a rejection or override decision.

    Attributes:
        LOW_QUALITY: Content quality below acceptable threshold.
        DUPLICATE: Content is a duplicate of previously seen content.
        CLICKBAIT: Title/hook is misleading or clickbait.
        NOT_RELEVANT: Content does not match the topic or audience.
        OUTDATED: Content is outdated or no longer timely.
        LOCAL_ONLY: Content is only relevant to a local audience.
        OTHER: Catch-all for uncategorized reasons.
    """

    LOW_QUALITY = "LOW_QUALITY"
    DUPLICATE = "DUPLICATE"
    CLICKBAIT = "CLICKBAIT"
    NOT_RELEVANT = "NOT_RELEVANT"
    OUTDATED = "OUTDATED"
    LOCAL_ONLY = "LOCAL_ONLY"
    OTHER = "OTHER"
