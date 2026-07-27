"""
Human Feedback Simulator — configurable reviewer policies.

Each policy decides APPROVE/REJECT/SKIP using only available information:
source quality, topic, category, freshness, confidence, recommendation score, keywords.

No ML, no LLM, no randomness — deterministic decisions based on policy rules.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from runtime.feedback.models import Decision


@dataclass
class ReviewContext:
    """Information available to a reviewer for making a decision."""

    article_id: str
    source: str
    category: str
    topic: str
    score: float
    recommendation: str
    source_quality: float
    freshness: str
    confidence: float
    keywords: list[str]
    similar_approved: int
    duplicates: int
    day_of_week: str
    iteration: int


@dataclass
class ReviewResult:
    """Result of a simulated review decision."""

    decision: Decision
    reason: str
    comment: Optional[str]
    policy_name: str
    response_time_ms: float


class FeedbackPolicy(ABC):
    """Base class for reviewer policies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable policy name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of the policy's behavior."""
        ...

    @abstractmethod
    def decide(self, ctx: ReviewContext, rng: random.Random) -> ReviewResult:
        """Make a decision based on the review context.

        Uses seeded RNG for reproducible but human-like decisions.
        """
        ...

    def _make_result(
        self, decision: Decision, reason: str, rng: random.Random,
        comment: Optional[str] = None,
    ) -> ReviewResult:
        """Create a ReviewResult with realistic response time."""
        # Response time: 2-15 seconds, policy-dependent
        base = 3.0 + rng.random() * 12.0
        return ReviewResult(
            decision=decision,
            reason=reason,
            comment=comment,
            policy_name=self.name,
            response_time_ms=base * 1000,
        )


class ConservativeReviewer(FeedbackPolicy):
    """Conservative reviewer — high standards, rejects more.

    Tends to reject anything below 0.85 confidence unless the source
    is extremely reliable. Approves only the best content.
    """

    @property
    def name(self) -> str:
        return "conservative"

    @property
    def description(self) -> str:
        return "High standards — rejects most, approves only excellent content"

    def decide(self, ctx: ReviewContext, rng: random.Random) -> ReviewResult:
        # Skip if confidence is very low
        if ctx.confidence < 0.30:
            return self._make_result(Decision.SKIP, "low_confidence", rng)

        # Reject if confidence below threshold
        if ctx.confidence < 0.60:
            reason = rng.choice(["low_relevance", "low_quality", "not_channel_fit"])
            return self._make_result(Decision.REJECT, reason, rng)

        # Reject if source quality is poor
        if ctx.source_quality < 0.50:
            return self._make_result(Decision.REJECT, "unreliable_source", rng)

        # Reject duplicates
        if ctx.duplicates > 2:
            return self._make_result(Decision.REJECT, "duplicate", rng)

        # Approve only high confidence + good source
        if ctx.confidence >= 0.85 and ctx.source_quality >= 0.70:
            return self._make_result(Decision.APPROVE, "other", rng)

        # Reject medium content (conservative bias)
        if ctx.confidence < 0.80:
            reason = rng.choice(["low_relevance", "incomplete"])
            return self._make_result(Decision.REJECT, reason, rng)

        return self._make_result(Decision.APPROVE, "other", rng)


class BalancedReviewer(FeedbackPolicy):
    """Balanced reviewer — fair, considers all factors.

    Weighs confidence, source quality, and freshness proportionally.
    Most human-like behavior.
    """

    @property
    def name(self) -> str:
        return "balanced"

    @property
    def description(self) -> str:
        return "Fair and balanced — considers all factors proportionally"

    def decide(self, ctx: ReviewContext, rng: random.Random) -> ReviewResult:
        # Skip if very low confidence
        if ctx.confidence < 0.25:
            return self._make_result(Decision.SKIP, "low_confidence", rng)

        # Calculate composite score
        freshness_map = {"very high": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
        fresh_score = freshness_map.get(ctx.freshness.lower(), 0.5)

        composite = (
            ctx.confidence * 0.35
            + ctx.source_quality * 0.25
            + fresh_score * 0.20
            + (ctx.score * 0.20)
        )

        # Adjust for duplicates
        if ctx.duplicates > 0:
            composite -= 0.1 * ctx.duplicates

        # Adjust for similar approved (positive signal)
        if ctx.similar_approved > 10:
            composite += 0.05

        # Decision thresholds
        if composite >= 0.70:
            return self._make_result(Decision.APPROVE, "other", rng)
        elif composite < 0.40:
            reason = rng.choice(["low_relevance", "low_quality", "clickbait"])
            return self._make_result(Decision.REJECT, reason, rng)
        else:
            # Borderline — random based on slight preference
            if rng.random() < 0.4:
                return self._make_result(Decision.APPROVE, "other", rng)
            reason = rng.choice(["low_relevance", "incomplete"])
            return self._make_result(Decision.REJECT, reason, rng)


class AggressiveReviewer(FeedbackPolicy):
    """Aggressive reviewer — approves more, lower bar.

    Approves most content unless it's clearly bad. High throughput.
    """

    @property
    def name(self) -> str:
        return "aggressive"

    @property
    def description(self) -> str:
        return "High throughput — approves most, rejects only bad content"

    def decide(self, ctx: ReviewContext, rng: random.Random) -> ReviewResult:
        # Skip only if extremely low
        if ctx.confidence < 0.15:
            return self._make_result(Decision.SKIP, "low_confidence", rng)

        # Reject only clearly bad
        if ctx.confidence < 0.30 and ctx.source_quality < 0.40:
            return self._make_result(Decision.REJECT, "unreliable_source", rng)

        if ctx.duplicates > 3:
            return self._make_result(Decision.REJECT, "duplicate", rng)

        # Approve everything else
        return self._make_result(Decision.APPROVE, "other", rng)


class QualityFocusedReviewer(FeedbackPolicy):
    """Quality-focused reviewer — prioritizes source quality and content depth.

    Cares most about source reputation and content quality signals.
    """

    @property
    def name(self) -> str:
        return "quality_focused"

    @property
    def description(self) -> str:
        return "Quality-first — prioritizes source reputation and content depth"

    def decide(self, ctx: ReviewContext, rng: random.Random) -> ReviewResult:
        if ctx.confidence < 0.20:
            return self._make_result(Decision.SKIP, "low_confidence", rng)

        # Source quality is the primary factor
        if ctx.source_quality >= 0.80:
            if ctx.confidence >= 0.60:
                return self._make_result(Decision.APPROVE, "other", rng)
            return self._make_result(Decision.REJECT, "low_quality", rng)

        if ctx.source_quality < 0.50:
            return self._make_result(Decision.REJECT, "unreliable_source", rng)

        # Medium source — need good confidence
        if ctx.confidence >= 0.75:
            return self._make_result(Decision.APPROVE, "other", rng)

        reason = rng.choice(["low_quality", "incomplete", "not_channel_fit"])
        return self._make_result(Decision.REJECT, reason, rng)


class GamingFocusedReviewer(FeedbackPolicy):
    """Gaming-focused reviewer — prefers gaming content, rejects non-gaming.

    Has strong preference for gaming category. Rejects AI/tech unless
    they have very high scores.
    """

    @property
    def name(self) -> str:
        return "gaming_focused"

    @property
    def description(self) -> str:
        return "Gaming-preferring — strongly favors gaming content"

    def decide(self, ctx: ReviewContext, rng: random.Random) -> ReviewResult:
        if ctx.confidence < 0.20:
            return self._make_result(Decision.SKIP, "low_confidence", rng)

        is_gaming = ctx.category.lower() == "gaming"

        if is_gaming:
            # Gaming: approve if decent
            if ctx.confidence >= 0.50:
                return self._make_result(Decision.APPROVE, "other", rng)
            return self._make_result(Decision.REJECT, "low_relevance", rng)

        # Non-gaming: reject unless exceptional
        if ctx.confidence >= 0.90 and ctx.source_quality >= 0.80:
            return self._make_result(Decision.APPROVE, "other", rng)

        return self._make_result(Decision.REJECT, "not_channel_fit", rng)


class ProgrammingFocusedReviewer(FeedbackPolicy):
    """Programming-focused reviewer — prefers programming content.

    Strong preference for programming category and technical depth.
    Rejects gaming and lifestyle content.
    """

    @property
    def name(self) -> str:
        return "programming_focused"

    @property
    def description(self) -> str:
        return "Programming-preferring — favors technical content"

    def decide(self, ctx: ReviewContext, rng: random.Random) -> ReviewResult:
        if ctx.confidence < 0.20:
            return self._make_result(Decision.SKIP, "low_confidence", rng)

        is_programming = ctx.category.lower() == "programming"
        is_ai_tech = ctx.category.lower() in ("ai", "tech")

        if is_programming:
            if ctx.confidence >= 0.55:
                return self._make_result(Decision.APPROVE, "other", rng)
            return self._make_result(Decision.REJECT, "low_quality", rng)

        if is_ai_tech:
            # AI/tech is acceptable if good quality
            if ctx.confidence >= 0.75 and ctx.source_quality >= 0.70:
                return self._make_result(Decision.APPROVE, "other", rng)
            return self._make_result(Decision.REJECT, "not_channel_fit", rng)

        # Gaming/startups: reject unless exceptional
        if ctx.confidence >= 0.90:
            return self._make_result(Decision.APPROVE, "other", rng)

        return self._make_result(Decision.REJECT, "not_channel_fit", rng)


# ── Policy Registry ──────────────────────────────────────────────────

POLICIES: dict[str, type[FeedbackPolicy]] = {
    "conservative": ConservativeReviewer,
    "balanced": BalancedReviewer,
    "aggressive": AggressiveReviewer,
    "quality_focused": QualityFocusedReviewer,
    "gaming_focused": GamingFocusedReviewer,
    "programming_focused": ProgrammingFocusedReviewer,
}


def get_policy(name: str) -> FeedbackPolicy:
    """Get a reviewer policy by name."""
    cls = POLICIES.get(name)
    if cls is None:
        available = ", ".join(sorted(POLICIES.keys()))
        raise ValueError(
            f"Unknown feedback policy: {name!r}. Available: {available}"
        )
    return cls()


def list_policies() -> list[dict[str, str]]:
    """List all available policies with their descriptions."""
    return [
        {"name": p.name, "description": p.description}
        for p in [cls() for cls in POLICIES.values()]
    ]
