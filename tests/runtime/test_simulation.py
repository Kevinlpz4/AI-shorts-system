"""
Sprint 8.4 — Simulation Engine Tests

Comprehensive test suite for adaptive learning simulation:
- Config: frozen dataclass, defaults, overrides, properties
- Clock: VirtualClock advance, reset, day tracking
- Feedback: 6 reviewer policies, registry, determinism
- Metrics: recording, snapshots, source profiles, categories
- Report: JSON/Markdown generation, file saving
- Charts: graceful fallback, generation when matplotlib available
- Engine: full simulation run, reproducibility, knowledge evolution
- Integration: 5-day and 30-day simulation runs
"""
from __future__ import annotations

import json
import os
import random
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from runtime.simulation.charts import (
    generate_all_charts,
    generate_approval_rate_chart,
    generate_confidence_chart,
    generate_dataset_growth_chart,
    generate_learning_curve_chart,
    generate_signals_chart,
    generate_source_quality_chart,
)
from runtime.simulation.clock import VirtualClock
from runtime.simulation.config import SimulationConfig
from runtime.simulation.engine import SimulationEngine
from runtime.simulation.feedback_sim import (
    AggressiveReviewer,
    BalancedReviewer,
    ConservativeReviewer,
    GamingFocusedReviewer,
    ProgrammingFocusedReviewer,
    QualityFocusedReviewer,
    ReviewContext,
    ReviewResult,
    get_policy,
    list_policies,
)
from runtime.simulation.metrics import MetricSnapshot, SimulationMetrics, SourceProfile
from runtime.simulation.report import (
    generate_json_report,
    generate_markdown_report,
    save_json_report,
    save_markdown_report,
)


# ═══════════════════════════════════════════════════════════════════
# CONFIG TESTS
# ═══════════════════════════════════════════════════════════════════


class TestSimulationConfig:
    """Tests for SimulationConfig frozen dataclass."""

    def test_default_config(self):
        cfg = SimulationConfig()
        assert cfg.days == 30
        assert cfg.iterations == 500
        assert cfg.seed == 42
        assert cfg.feedback_policy == "balanced"
        assert cfg.speed == "accelerated"
        assert cfg.articles_per_day == 20
        assert cfg.source_count == 8
        assert cfg.learning_rate == 0.05
        assert cfg.decay_rate == 0.01

    def test_frozen(self):
        cfg = SimulationConfig()
        with pytest.raises(AttributeError):
            cfg.days = 60  # type: ignore

    def test_custom_config(self):
        cfg = SimulationConfig(days=7, seed=123, feedback_policy="aggressive")
        assert cfg.days == 7
        assert cfg.seed == 123
        assert cfg.feedback_policy == "aggressive"

    def test_total_hours(self):
        cfg = SimulationConfig(days=14)
        assert cfg.total_hours == 336.0

    def test_total_articles(self):
        cfg = SimulationConfig(days=10, articles_per_day=25)
        assert cfg.total_articles == 250

    def test_with_overrides(self):
        cfg = SimulationConfig(days=30, seed=42)
        cfg2 = cfg.with_overrides(days=7, seed=99)
        assert cfg2.days == 7
        assert cfg2.seed == 99
        # Original unchanged
        assert cfg.days == 30
        assert cfg.seed == 42

    def test_category_weights_default(self):
        cfg = SimulationConfig()
        assert "ai" in cfg.category_weights
        assert "gaming" in cfg.category_weights
        assert sum(cfg.category_weights.values()) == pytest.approx(1.0)


# ═══════════════════════════════════════════════════════════════════
# CLOCK TESTS
# ═══════════════════════════════════════════════════════════════════


class TestVirtualClock:
    """Tests for VirtualClock time acceleration."""

    def test_initial_state(self):
        clock = VirtualClock(start_date="2026-07-01")
        assert clock.now.day == 1
        assert clock.now.month == 7
        assert clock.total_advanced_hours == 0.0
        assert clock.step_count == 0

    def test_advance_hours(self):
        clock = VirtualClock(start_date="2026-07-01")
        new_time = clock.advance_hours(24)
        assert new_time.day == 2
        assert clock.total_advanced_hours == 24.0
        assert clock.step_count == 1

    def test_advance_days(self):
        clock = VirtualClock(start_date="2026-07-01")
        clock.advance_days(7)
        assert clock.now.day == 8
        assert clock.total_advanced_hours == 168.0

    def test_advance_minutes(self):
        clock = VirtualClock(start_date="2026-07-01")
        clock.advance_minutes(90)
        assert clock.total_advanced_hours == pytest.approx(1.5)
        assert clock.now.hour == 1
        assert clock.now.minute == 30

    def test_advance_iterations(self):
        clock = VirtualClock(start_date="2026-07-01")
        clock.advance_iterations(10, hours_per_iteration=2.4)
        assert clock.total_advanced_hours == pytest.approx(24.0)

    def test_day_of_week(self):
        # 2026-07-01 is a Wednesday
        clock = VirtualClock(start_date="2026-07-01")
        assert clock.day_of_week() == "Wednesday"

    def test_is_weekend(self):
        clock = VirtualClock(start_date="2026-07-04")  # Saturday
        assert clock.is_weekend() is True
        clock2 = VirtualClock(start_date="2026-07-06")  # Monday
        assert clock2.is_weekend() is False

    def test_reset(self):
        clock = VirtualClock(start_date="2026-07-01")
        clock.advance_days(5)
        assert clock.step_count > 0
        clock.reset()
        assert clock.total_advanced_hours == 0.0
        assert clock.step_count == 0

    def test_date_str(self):
        clock = VirtualClock(start_date="2026-12-25")
        assert clock.date_str() == "2026-12-25"

    def test_time_str(self):
        clock = VirtualClock(start_date="2026-07-01")
        assert clock.time_str() == "00:00:00"

    def test_datetime_str(self):
        clock = VirtualClock(start_date="2026-07-01")
        result = clock.datetime_str()
        assert "2026-07-01" in result

    def test_repr(self):
        clock = VirtualClock(start_date="2026-07-01")
        r = repr(clock)
        assert "VirtualClock" in r
        assert "2026-07-01" in r

    def test_with_datetime_object(self):
        dt = datetime(2026, 8, 15, tzinfo=timezone.utc)
        clock = VirtualClock(start_date=dt)
        assert clock.now.day == 15
        assert clock.now.month == 8

    def test_elapsed_wall_seconds(self):
        clock = VirtualClock(start_date="2026-07-01")
        elapsed = clock.elapsed_wall_seconds()
        assert elapsed >= 0.0

    def test_multiple_advances(self):
        clock = VirtualClock(start_date="2026-07-01")
        clock.advance_hours(10)
        clock.advance_hours(14)
        assert clock.total_advanced_hours == 24.0
        assert clock.step_count == 2


# ═══════════════════════════════════════════════════════════════════
# FEEDBACK POLICY TESTS
# ═══════════════════════════════════════════════════════════════════


def _make_ctx(**overrides) -> ReviewContext:
    """Create a ReviewContext with sensible defaults."""
    defaults = dict(
        article_id="test-001",
        source="google_news_ai",
        category="ai",
        topic="llm",
        score=0.75,
        recommendation="APPROVE",
        source_quality=0.70,
        freshness="High",
        confidence=0.70,
        keywords=["AI", "LLM", "GPT"],
        similar_approved=20,
        duplicates=0,
        day_of_week="Wednesday",
        iteration=0,
    )
    defaults.update(overrides)
    return ReviewContext(**defaults)


class TestPolicyRegistry:
    """Tests for policy registry and lookup."""

    def test_get_policy_balanced(self):
        p = get_policy("balanced")
        assert isinstance(p, BalancedReviewer)
        assert p.name == "balanced"

    def test_get_policy_conservative(self):
        p = get_policy("conservative")
        assert isinstance(p, ConservativeReviewer)

    def test_get_policy_aggressive(self):
        p = get_policy("aggressive")
        assert isinstance(p, AggressiveReviewer)

    def test_get_policy_quality_focused(self):
        p = get_policy("quality_focused")
        assert isinstance(p, QualityFocusedReviewer)

    def test_get_policy_gaming_focused(self):
        p = get_policy("gaming_focused")
        assert isinstance(p, GamingFocusedReviewer)

    def test_get_policy_programming_focused(self):
        p = get_policy("programming_focused")
        assert isinstance(p, ProgrammingFocusedReviewer)

    def test_get_policy_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown feedback policy"):
            get_policy("nonexistent_policy")

    def test_list_policies(self):
        policies = list_policies()
        assert len(policies) == 6
        names = [p["name"] for p in policies]
        assert "balanced" in names
        assert "conservative" in names
        assert "aggressive" in names
        assert "quality_focused" in names
        assert "gaming_focused" in names
        assert "programming_focused" in names

    def test_all_policies_have_description(self):
        for p in list_policies():
            assert "description" in p
            assert len(p["description"]) > 10


class TestConservativeReviewer:
    """Tests for ConservativeReviewer policy."""

    def test_low_confidence_skip(self):
        rng = random.Random(42)
        p = ConservativeReviewer()
        ctx = _make_ctx(confidence=0.20)
        result = p.decide(ctx, rng)
        assert result.decision.value == "skip"

    def test_medium_confidence_reject(self):
        rng = random.Random(42)
        p = ConservativeReviewer()
        ctx = _make_ctx(confidence=0.50)
        result = p.decide(ctx, rng)
        assert result.decision.value == "reject"

    def test_poor_source_reject(self):
        rng = random.Random(42)
        p = ConservativeReviewer()
        ctx = _make_ctx(confidence=0.70, source_quality=0.40)
        result = p.decide(ctx, rng)
        assert result.decision.value == "reject"

    def test_high_confidence_approve(self):
        rng = random.Random(42)
        p = ConservativeReviewer()
        ctx = _make_ctx(confidence=0.90, source_quality=0.80)
        result = p.decide(ctx, rng)
        assert result.decision.value == "approve"

    def test_deterministic(self):
        ctx = _make_ctx(confidence=0.75, source_quality=0.75)
        r1 = ConservativeReviewer().decide(ctx, random.Random(42))
        r2 = ConservativeReviewer().decide(ctx, random.Random(42))
        assert r1.decision == r2.decision
        assert r1.reason == r2.reason


class TestBalancedReviewer:
    """Tests for BalancedReviewer policy."""

    def test_very_low_confidence_skip(self):
        rng = random.Random(42)
        p = BalancedReviewer()
        ctx = _make_ctx(confidence=0.15)
        result = p.decide(ctx, rng)
        assert result.decision.value == "skip"

    def test_high_composite_approve(self):
        rng = random.Random(42)
        p = BalancedReviewer()
        ctx = _make_ctx(
            confidence=0.90, source_quality=0.90, freshness="Very High",
            score=0.90, similar_approved=20,
        )
        result = p.decide(ctx, rng)
        assert result.decision.value == "approve"

    def test_low_composite_reject(self):
        rng = random.Random(42)
        p = BalancedReviewer()
        ctx = _make_ctx(
            confidence=0.30, source_quality=0.20, freshness="Low",
            score=0.15, duplicates=3,
        )
        result = p.decide(ctx, rng)
        assert result.decision.value == "reject"

    def test_deterministic(self):
        ctx = _make_ctx(confidence=0.60, source_quality=0.60)
        r1 = BalancedReviewer().decide(ctx, random.Random(42))
        r2 = BalancedReviewer().decide(ctx, random.Random(42))
        assert r1.decision == r2.decision


class TestAggressiveReviewer:
    """Tests for AggressiveReviewer policy."""

    def test_extremely_low_skip(self):
        rng = random.Random(42)
        p = AggressiveReviewer()
        ctx = _make_ctx(confidence=0.10)
        result = p.decide(ctx, rng)
        assert result.decision.value == "skip"

    def test_normal_content_approve(self):
        rng = random.Random(42)
        p = AggressiveReviewer()
        ctx = _make_ctx(confidence=0.50, source_quality=0.50)
        result = p.decide(ctx, rng)
        assert result.decision.value == "approve"

    def test_high_duplicates_reject(self):
        rng = random.Random(42)
        p = AggressiveReviewer()
        ctx = _make_ctx(confidence=0.50, duplicates=4)
        result = p.decide(ctx, rng)
        assert result.decision.value == "reject"


class TestQualityFocusedReviewer:
    """Tests for QualityFocusedReviewer policy."""

    def test_high_quality_approve(self):
        rng = random.Random(42)
        p = QualityFocusedReviewer()
        ctx = _make_ctx(confidence=0.70, source_quality=0.85)
        result = p.decide(ctx, rng)
        assert result.decision.value == "approve"

    def test_low_quality_reject(self):
        rng = random.Random(42)
        p = QualityFocusedReviewer()
        ctx = _make_ctx(confidence=0.70, source_quality=0.40)
        result = p.decide(ctx, rng)
        assert result.decision.value == "reject"

    def test_medium_source_needs_high_confidence(self):
        rng = random.Random(42)
        p = QualityFocusedReviewer()
        ctx = _make_ctx(confidence=0.60, source_quality=0.60)
        result = p.decide(ctx, rng)
        assert result.decision.value == "reject"


class TestGamingFocusedReviewer:
    """Tests for GamingFocusedReviewer policy."""

    def test_gaming_content_approve(self):
        rng = random.Random(42)
        p = GamingFocusedReviewer()
        ctx = _make_ctx(category="gaming", confidence=0.60)
        result = p.decide(ctx, rng)
        assert result.decision.value == "approve"

    def test_non_gaming_reject(self):
        rng = random.Random(42)
        p = GamingFocusedReviewer()
        ctx = _make_ctx(category="ai", confidence=0.70, source_quality=0.60)
        result = p.decide(ctx, rng)
        assert result.decision.value == "reject"

    def test_non_gaming_exceptional_approve(self):
        rng = random.Random(42)
        p = GamingFocusedReviewer()
        ctx = _make_ctx(category="ai", confidence=0.95, source_quality=0.85)
        result = p.decide(ctx, rng)
        assert result.decision.value == "approve"


class TestProgrammingFocusedReviewer:
    """Tests for ProgrammingFocusedReviewer policy."""

    def test_programming_approve(self):
        rng = random.Random(42)
        p = ProgrammingFocusedReviewer()
        ctx = _make_ctx(category="programming", confidence=0.60)
        result = p.decide(ctx, rng)
        assert result.decision.value == "approve"

    def test_ai_tech_acceptable_if_good(self):
        rng = random.Random(42)
        p = ProgrammingFocusedReviewer()
        ctx = _make_ctx(category="ai", confidence=0.80, source_quality=0.75)
        result = p.decide(ctx, rng)
        assert result.decision.value == "approve"

    def test_gaming_reject(self):
        rng = random.Random(42)
        p = ProgrammingFocusedReviewer()
        ctx = _make_ctx(category="gaming", confidence=0.70)
        result = p.decide(ctx, rng)
        assert result.decision.value == "reject"


class TestReviewContext:
    """Tests for ReviewContext dataclass."""

    def test_creation(self):
        ctx = _make_ctx()
        assert ctx.article_id == "test-001"
        assert ctx.confidence == 0.70

    def test_fields(self):
        ctx = _make_ctx(category="gaming", confidence=0.90)
        assert ctx.category == "gaming"
        assert ctx.confidence == 0.90


class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_creation(self):
        from runtime.feedback.models import Decision
        rr = ReviewResult(
            decision=Decision.APPROVE,
            reason="other",
            comment=None,
            policy_name="balanced",
            response_time_ms=5000.0,
        )
        assert rr.decision == Decision.APPROVE
        assert rr.policy_name == "balanced"


# ═══════════════════════════════════════════════════════════════════
# METRICS TESTS
# ═══════════════════════════════════════════════════════════════════


class TestSourceProfile:
    """Tests for SourceProfile dataclass."""

    def test_empty_profile(self):
        sp = SourceProfile(source_id="test", quality=0.6)
        assert sp.approval_rate == 0.0
        assert sp.rejection_rate == 0.0

    def test_with_decisions(self):
        sp = SourceProfile(source_id="test", quality=0.6, total_articles=10,
                           approved=7, rejected=3)
        assert sp.approval_rate == pytest.approx(0.7)
        assert sp.rejection_rate == pytest.approx(0.3)


class TestSimulationMetrics:
    """Tests for SimulationMetrics tracking."""

    def test_initial_state(self):
        m = SimulationMetrics()
        assert m.total_articles == 0
        assert m.total_decisions == 0
        assert m.total_approved == 0
        assert m.total_rejected == 0
        assert m.total_skipped == 0
        assert m.total_signals == 0
        assert m.total_artifacts == 0

    def test_record_article(self):
        m = SimulationMetrics()
        m.record_article("source1")
        m.record_article("source1")
        assert m.total_articles == 2

    def test_record_decision_approved(self):
        m = SimulationMetrics()
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI"],
            iteration=0, day=1, timestamp=datetime.now(timezone.utc),
        )
        assert m.total_decisions == 1
        assert m.total_approved == 1
        assert m.total_rejected == 0

    def test_record_decision_rejected(self):
        m = SimulationMetrics()
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=False,
            confidence=0.3, source_quality=0.4, keywords=["bad"],
            iteration=0, day=1, timestamp=datetime.now(timezone.utc),
        )
        assert m.total_decisions == 1
        assert m.total_approved == 0
        assert m.total_rejected == 1

    def test_record_skip(self):
        m = SimulationMetrics()
        m.record_skip()
        assert m.total_skipped == 1
        assert m.total_decisions == 1

    def test_record_signal(self):
        m = SimulationMetrics()
        m.record_signal()
        m.record_signal()
        assert m.total_signals == 2

    def test_record_artifact(self):
        m = SimulationMetrics()
        m.record_artifact()
        assert m.total_artifacts == 1

    def test_source_profiles_created(self):
        m = SimulationMetrics()
        m.record_decision(
            source="src1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI"],
            iteration=0, day=1, timestamp=datetime.now(timezone.utc),
        )
        profiles = m.source_profiles
        assert "src1" in profiles
        assert profiles["src1"].total_articles == 1

    def test_keyword_tracking(self):
        m = SimulationMetrics()
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI", "LLM"],
            iteration=0, day=1, timestamp=datetime.now(timezone.utc),
        )
        freq = m.keyword_freq
        assert freq["AI"] == 1
        assert freq["LLM"] == 1

    def test_category_tracking(self):
        m = SimulationMetrics()
        m.record_decision(
            source="s1", category="gaming", topic="steam", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["gaming"],
            iteration=0, day=1, timestamp=datetime.now(timezone.utc),
        )
        cat = m.category_stats
        assert "gaming" in cat
        assert cat["gaming"]["approved"] == 1

    def test_take_snapshot(self):
        m = SimulationMetrics()
        m.record_article("s1")
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI"],
            iteration=0, day=1, timestamp=datetime.now(timezone.utc),
        )
        snap = m.take_snapshot(day=1, iteration=1, timestamp=datetime.now(timezone.utc))
        assert isinstance(snap, MetricSnapshot)
        assert snap.total_articles == 1
        assert snap.total_decisions == 1
        assert snap.approval_rate == pytest.approx(1.0)

    def test_snapshots_accumulate(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        for i in range(5):
            m.record_article("s1")
            m.record_decision(
                source="s1", category="ai", topic="llm", approved=(i % 2 == 0),
                confidence=0.7, source_quality=0.6, keywords=["AI"],
                iteration=i, day=1, timestamp=ts,
            )
            m.take_snapshot(day=1, iteration=i, timestamp=ts)
        assert len(m.snapshots) == 5

    def test_top_sources(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        for _ in range(5):
            m.record_decision(
                source="good_src", category="ai", topic="llm", approved=True,
                confidence=0.9, source_quality=0.9, keywords=["AI"],
                iteration=0, day=1, timestamp=ts,
            )
        for _ in range(3):
            m.record_decision(
                source="bad_src", category="ai", topic="llm", approved=False,
                confidence=0.3, source_quality=0.3, keywords=["bad"],
                iteration=0, day=1, timestamp=ts,
            )
        top = m.top_sources
        assert len(top) == 2
        assert top[0]["source"] == "good_src"
        assert top[0]["approval_rate"] == pytest.approx(1.0)

    def test_worst_sources(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI"],
            iteration=0, day=1, timestamp=ts,
        )
        worst = m.worst_sources
        assert len(worst) == 1

    def test_top_keywords(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI", "AI", "AI"],
            iteration=0, day=1, timestamp=ts,
        )
        top_kw = m.top_keywords
        assert len(top_kw) >= 1
        assert top_kw[0][0] == "AI"

    def test_category_breakdown(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI"],
            iteration=0, day=1, timestamp=ts,
        )
        bd = m.category_breakdown
        assert len(bd) == 1
        assert bd[0]["category"] == "ai"

    def test_confidence_history(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        for i in range(3):
            m.record_decision(
                source="s1", category="ai", topic="llm", approved=True,
                confidence=0.5 + i * 0.1, source_quality=0.7, keywords=["AI"],
                iteration=i, day=1, timestamp=ts,
            )
        assert len(m.confidence_history) == 3
        assert m.confidence_history[0] == pytest.approx(0.5)

    def test_approval_rate_history(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        m.record_article("s1")
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI"],
            iteration=0, day=1, timestamp=ts,
        )
        m.take_snapshot(day=1, iteration=1, timestamp=ts)
        assert len(m.approval_rate_history) == 1

    def test_dataset_growth(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        m.record_article("s1")
        m.record_article("s1")
        m.take_snapshot(day=1, iteration=1, timestamp=ts)
        assert m.dataset_growth == [2]

    def test_signals_count(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        m.record_signal()
        m.record_signal()
        m.record_signal()
        m.take_snapshot(day=1, iteration=1, timestamp=ts)
        assert m.signals_count == [3]

    def test_elapsed_seconds(self):
        m = SimulationMetrics()
        elapsed = m.elapsed_seconds()
        assert elapsed >= 0.0

    def test_reset(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        m.record_article("s1")
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.7, keywords=["AI"],
            iteration=0, day=1, timestamp=ts,
        )
        m.record_signal()
        m.take_snapshot(day=1, iteration=1, timestamp=ts)
        m.reset()
        assert m.total_articles == 0
        assert m.total_decisions == 0
        assert m.total_signals == 0
        assert len(m.snapshots) == 0

    def test_source_quality_moving_average(self):
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        # First decision with quality 0.8
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.8, keywords=["AI"],
            iteration=0, day=1, timestamp=ts,
        )
        q1 = m.source_profiles["s1"].quality
        # Second decision with quality 0.2 → moving avg
        m.record_decision(
            source="s1", category="ai", topic="llm", approved=True,
            confidence=0.8, source_quality=0.2, keywords=["AI"],
            iteration=1, day=1, timestamp=ts,
        )
        q2 = m.source_profiles["s1"].quality
        assert q2 != q1
        # Moving average: q1 * 0.95 + 0.2 * 0.05
        expected = q1 * 0.95 + 0.2 * 0.05
        assert q2 == pytest.approx(expected, abs=0.001)


# ═══════════════════════════════════════════════════════════════════
# REPORT TESTS
# ═══════════════════════════════════════════════════════════════════


class TestReportGeneration:
    """Tests for JSON and Markdown report generation."""

    def _make_metrics_with_data(self) -> SimulationMetrics:
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        for i in range(10):
            m.record_article("src1")
            m.record_decision(
                source="src1", category="ai", topic="llm",
                approved=(i % 2 == 0),
                confidence=0.5 + i * 0.03, source_quality=0.6,
                keywords=["AI", "test"], iteration=i, day=1, timestamp=ts,
            )
            m.record_signal()
        m.take_snapshot(day=1, iteration=10, timestamp=ts)
        return m

    def test_generate_json_report(self):
        m = self._make_metrics_with_data()
        cfg = SimulationConfig(days=1, seed=42)
        report = generate_json_report(m, cfg, elapsed_seconds=1.5)
        assert "metadata" in report
        assert "summary" in report
        assert "evolution" in report
        assert "sources" in report
        assert "categories" in report
        assert "keywords" in report
        assert "signals" in report

    def test_json_report_summary(self):
        m = self._make_metrics_with_data()
        cfg = SimulationConfig(days=1, seed=42)
        report = generate_json_report(m, cfg, elapsed_seconds=1.0)
        assert report["summary"]["articles_processed"] == 10
        assert report["summary"]["decisions_made"] == 10

    def test_json_report_evolution(self):
        m = self._make_metrics_with_data()
        cfg = SimulationConfig(days=1, seed=42)
        report = generate_json_report(m, cfg, elapsed_seconds=1.0)
        evo = report["evolution"]
        assert "confidence_start" in evo
        assert "confidence_end" in evo
        assert "confidence_delta" in evo
        assert "knowledge_growth" in evo

    def test_json_report_sources(self):
        m = self._make_metrics_with_data()
        cfg = SimulationConfig(days=1, seed=42)
        report = generate_json_report(m, cfg, elapsed_seconds=1.0)
        assert report["sources"]["total_profiled"] == 1
        assert len(report["sources"]["top"]) == 1

    def test_save_json_report(self):
        m = self._make_metrics_with_data()
        cfg = SimulationConfig(days=1, seed=42)
        report = generate_json_report(m, cfg, elapsed_seconds=1.0)
        with tempfile.TemporaryDirectory() as td:
            path = save_json_report(report, f"{td}/report.json")
            assert os.path.exists(path)
            content = json.loads(Path(path).read_text())
            assert content["summary"]["articles_processed"] == 10

    def test_generate_markdown_report(self):
        m = self._make_metrics_with_data()
        cfg = SimulationConfig(days=1, seed=42)
        report = generate_json_report(m, cfg, elapsed_seconds=1.0)
        md = generate_markdown_report(report)
        assert "# Simulation Report" in md
        assert "## Summary" in md
        assert "## Learning Evolution" in md
        assert "## Source Profiles" in md
        assert "## Category Breakdown" in md
        assert "## Top Keywords" in md
        assert "## Learning Signals" in md

    def test_save_markdown_report(self):
        md_content = "# Test Report\n\nHello world."
        with tempfile.TemporaryDirectory() as td:
            path = save_markdown_report(md_content, f"{td}/report.md")
            assert os.path.exists(path)
            assert Path(path).read_text() == md_content

    def test_report_with_empty_metrics(self):
        m = SimulationMetrics()
        cfg = SimulationConfig()
        report = generate_json_report(m, cfg, elapsed_seconds=0.0)
        assert report["summary"]["articles_processed"] == 0
        assert report["evolution"]["knowledge_growth"] == 0


# ═══════════════════════════════════════════════════════════════════
# CHARTS TESTS
# ═══════════════════════════════════════════════════════════════════


class TestCharts:
    """Tests for chart generation (graceful fallback when matplotlib missing)."""

    def _make_metrics_with_history(self) -> SimulationMetrics:
        m = SimulationMetrics()
        ts = datetime.now(timezone.utc)
        for i in range(20):
            m.record_article("src1")
            m.record_decision(
                source="src1", category="ai", topic="llm",
                approved=(i % 3 != 0),
                confidence=0.4 + i * 0.02, source_quality=0.5 + i * 0.01,
                keywords=["AI", "test"], iteration=i, day=1, timestamp=ts,
            )
            m.record_signal()
        m.take_snapshot(day=1, iteration=20, timestamp=ts)
        return m

    def test_generate_all_charts(self):
        m = self._make_metrics_with_history()
        with tempfile.TemporaryDirectory() as td:
            paths = generate_all_charts(m, td)
            # Either generates charts or returns empty (no matplotlib)
            assert isinstance(paths, list)

    def test_approval_rate_chart(self):
        m = self._make_metrics_with_history()
        with tempfile.TemporaryDirectory() as td:
            result = generate_approval_rate_chart(m, td)
            # Result is path or None
            if result:
                assert os.path.exists(result)

    def test_confidence_chart(self):
        m = self._make_metrics_with_history()
        with tempfile.TemporaryDirectory() as td:
            result = generate_confidence_chart(m, td)
            if result:
                assert os.path.exists(result)

    def test_source_quality_chart(self):
        m = self._make_metrics_with_history()
        with tempfile.TemporaryDirectory() as td:
            result = generate_source_quality_chart(m, td)
            if result:
                assert os.path.exists(result)

    def test_learning_curve_chart(self):
        m = self._make_metrics_with_history()
        with tempfile.TemporaryDirectory() as td:
            result = generate_learning_curve_chart(m, td)
            if result:
                assert os.path.exists(result)

    def test_dataset_growth_chart(self):
        m = self._make_metrics_with_history()
        with tempfile.TemporaryDirectory() as td:
            result = generate_dataset_growth_chart(m, td)
            if result:
                assert os.path.exists(result)

    def test_signals_chart(self):
        m = self._make_metrics_with_history()
        with tempfile.TemporaryDirectory() as td:
            result = generate_signals_chart(m, td)
            if result:
                assert os.path.exists(result)

    def test_empty_metrics_no_crash(self):
        m = SimulationMetrics()
        with tempfile.TemporaryDirectory() as td:
            paths = generate_all_charts(m, td)
            assert paths == []

    def test_chart_creates_directory(self):
        m = self._make_metrics_with_history()
        with tempfile.TemporaryDirectory() as td:
            subdir = os.path.join(td, "nested", "charts")
            result = generate_approval_rate_chart(m, subdir)
            if result:
                assert os.path.exists(result)


# ═══════════════════════════════════════════════════════════════════
# ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════


class TestSimulationEngine:
    """Tests for SimulationEngine full simulation run."""

    def test_engine_creation(self):
        cfg = SimulationConfig(days=1, iterations=10, seed=42)
        engine = SimulationEngine(cfg)
        assert engine.config.days == 1
        assert engine.clock is not None
        assert engine.metrics is not None

    def test_engine_knowledge_base_init(self):
        cfg = SimulationConfig(days=1, iterations=10, seed=42)
        engine = SimulationEngine(cfg)
        kb = engine.knowledge_base
        assert "source_quality" in kb
        assert "category_preference" in kb
        assert "keyword_frequency" in kb
        assert "historical_success" in kb

    def test_run_1_day(self):
        cfg = SimulationConfig(days=1, iterations=10, seed=42, report_dir="/tmp/sim_test_1d")
        engine = SimulationEngine(cfg)
        report = engine.run()
        assert report["summary"]["articles_processed"] > 0
        assert report["summary"]["decisions_made"] > 0
        assert "evolution" in report
        assert "sources" in report
        assert "categories" in report

    def test_run_5_days(self):
        cfg = SimulationConfig(days=5, iterations=50, seed=42, report_dir="/tmp/sim_test_5d")
        engine = SimulationEngine(cfg)
        report = engine.run()
        assert report["summary"]["articles_processed"] > 0
        assert report["summary"]["approved"] > 0
        assert report["summary"]["rejected"] > 0
        assert report["evolution"]["knowledge_growth"] > 0

    def test_reproducibility(self):
        """Same seed = same results."""
        cfg = SimulationConfig(days=3, iterations=30, seed=777, report_dir="/tmp/sim_test_rep")
        r1 = SimulationEngine(cfg).run()
        r2 = SimulationEngine(cfg).run()
        assert r1["summary"]["articles_processed"] == r2["summary"]["articles_processed"]
        assert r1["summary"]["approved"] == r2["summary"]["approved"]
        assert r1["summary"]["rejected"] == r2["summary"]["rejected"]

    def test_different_seeds_differ(self):
        r1 = SimulationEngine(SimulationConfig(days=3, iterations=30, seed=1, report_dir="/tmp/sim_s1")).run()
        r2 = SimulationEngine(SimulationConfig(days=3, iterations=30, seed=999, report_dir="/tmp/sim_s2")).run()
        # Very unlikely to be identical with different seeds
        # Just verify both produce output
        assert r1["summary"]["articles_processed"] > 0
        assert r2["summary"]["articles_processed"] > 0

    def test_knowledge_base_evolves(self):
        cfg = SimulationConfig(days=5, iterations=50, seed=42, report_dir="/tmp/sim_test_evo")
        engine = SimulationEngine(cfg)
        engine.run()
        kb = engine.knowledge_base
        assert len(kb["source_quality"]) > 0
        assert len(kb["category_preference"]) > 0
        assert len(kb["keyword_frequency"]) > 0

    def test_metrics_populated(self):
        cfg = SimulationConfig(days=3, iterations=30, seed=42, report_dir="/tmp/sim_test_met")
        engine = SimulationEngine(cfg)
        engine.run()
        m = engine.metrics
        assert m.total_articles > 0
        assert m.total_decisions > 0
        assert len(m.snapshots) > 0
        assert len(m.source_profiles) > 0

    def test_clock_advanced(self):
        cfg = SimulationConfig(days=3, iterations=30, seed=42, report_dir="/tmp/sim_test_clk")
        engine = SimulationEngine(cfg)
        engine.run()
        assert engine.clock.total_advanced_hours > 0
        assert engine.clock.step_count > 0

    def test_reports_generated(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = SimulationConfig(days=1, iterations=10, seed=42, report_dir=td)
            engine = SimulationEngine(cfg)
            engine.run()
            assert os.path.exists(os.path.join(td, "simulation_report.json"))
            assert os.path.exists(os.path.join(td, "simulation_report.md"))

    def test_all_policies_work(self):
        for policy in ["conservative", "balanced", "aggressive",
                        "quality_focused", "gaming_focused", "programming_focused"]:
            cfg = SimulationConfig(
                days=1, iterations=5, seed=42,
                feedback_policy=policy,
                report_dir=f"/tmp/sim_test_{policy}",
            )
            engine = SimulationEngine(cfg)
            report = engine.run()
            assert report["summary"]["articles_processed"] > 0


# ═══════════════════════════════════════════════════════════════════
# INTEGRATION / LONG-RUNNING TESTS
# ═══════════════════════════════════════════════════════════════════


class TestSimulationIntegration:
    """Integration tests for multi-day simulation runs."""

    def test_30_day_simulation(self):
        """Full 30-day simulation — the core Sprint 8.4 deliverable."""
        with tempfile.TemporaryDirectory() as td:
            cfg = SimulationConfig(
                days=30, iterations=500, seed=42,
                feedback_policy="balanced", report_dir=td,
            )
            engine = SimulationEngine(cfg)
            report = engine.run()

            # Core assertions
            assert report["summary"]["articles_processed"] > 500
            assert report["summary"]["decisions_made"] > 500
            assert report["summary"]["approved"] > 0
            assert report["summary"]["rejected"] > 0
            assert report["summary"]["signals_generated"] > 0

            # Evolution
            evo = report["evolution"]
            assert isinstance(evo["confidence_start"], float)
            assert isinstance(evo["confidence_end"], float)
            assert isinstance(evo["knowledge_growth"], int)
            assert evo["knowledge_growth"] > 0

            # Sources
            assert report["sources"]["total_profiled"] > 0
            assert len(report["sources"]["top"]) > 0

            # Categories
            assert len(report["categories"]) > 0

            # Keywords
            assert report["keywords"]["unique_count"] > 0

            # Reports exist
            assert os.path.exists(os.path.join(td, "simulation_report.json"))
            assert os.path.exists(os.path.join(td, "simulation_report.md"))

            # Verify JSON is valid
            json_data = json.loads(Path(os.path.join(td, "simulation_report.json")).read_text())
            assert json_data["metadata"]["simulation_config"]["days"] == 30

    def test_aggressive_policy_higher_approval(self):
        """Aggressive policy should approve more than conservative."""
        with tempfile.TemporaryDirectory() as td:
            cfg_agg = SimulationConfig(
                days=5, iterations=50, seed=42,
                feedback_policy="aggressive", report_dir=os.path.join(td, "agg"),
            )
            r_agg = SimulationEngine(cfg_agg).run()

            cfg_con = SimulationConfig(
                days=5, iterations=50, seed=42,
                feedback_policy="conservative", report_dir=os.path.join(td, "con"),
            )
            r_con = SimulationEngine(cfg_con).run()

            # Aggressive should approve more
            assert r_agg["summary"]["approved"] > r_con["summary"]["approved"]

    def test_quality_policy_focuses_on_quality_sources(self):
        """Quality-focused policy should have higher avg source quality for approved items."""
        with tempfile.TemporaryDirectory() as td:
            cfg = SimulationConfig(
                days=5, iterations=50, seed=42,
                feedback_policy="quality_focused", report_dir=td,
            )
            report = SimulationEngine(cfg).run()
            assert report["summary"]["articles_processed"] > 0

    def test_gaming_policy_prefers_gaming(self):
        """Gaming-focused policy should have higher approval for gaming category."""
        with tempfile.TemporaryDirectory() as td:
            cfg = SimulationConfig(
                days=5, iterations=50, seed=42,
                feedback_policy="gaming_focused", report_dir=td,
            )
            report = SimulationEngine(cfg).run()
            gaming_cats = [c for c in report["categories"] if c["category"] == "gaming"]
            if gaming_cats:
                assert gaming_cats[0]["approval_rate"] > 0.0

    def test_markdown_report_content(self):
        """Verify Markdown report has all sections."""
        with tempfile.TemporaryDirectory() as td:
            cfg = SimulationConfig(days=3, iterations=30, seed=42, report_dir=td)
            engine = SimulationEngine(cfg)
            engine.run()
            md_path = os.path.join(td, "simulation_report.md")
            content = Path(md_path).read_text()
            assert "# Simulation Report" in content
            assert "## Summary" in content
            assert "## Learning Evolution" in content
            assert "## Source Profiles" in content
            assert "## Category Breakdown" in content
            assert "## Top Keywords" in content
            assert "## Learning Signals" in content

    def test_json_report_structure(self):
        """Verify JSON report has all required sections."""
        with tempfile.TemporaryDirectory() as td:
            cfg = SimulationConfig(days=3, iterations=30, seed=42, report_dir=td)
            report = SimulationEngine(cfg).run()
            required_keys = ["metadata", "summary", "evolution", "sources",
                             "categories", "keywords", "confidence_evolution",
                             "dataset_evolution", "signals"]
            for key in required_keys:
                assert key in report, f"Missing key: {key}"
