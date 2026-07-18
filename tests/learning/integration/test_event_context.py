"""
Tests for EventContext — observability context for event traceability.

Validates: construction defaults, immutability, with_causation,
new_correlated, correlation chains, and causation chains.
"""
from __future__ import annotations

import pytest
from uuid import UUID, uuid4

from learning.integration.observability.event_context import EventContext


class TestEventContextConstruction:
    """Default construction and field setting."""

    def test_construction_defaults(self) -> None:
        ctx = EventContext()
        assert isinstance(ctx.event_id, UUID)
        assert ctx.correlation_id == ""
        assert ctx.causation_id is None
        assert ctx.occurred_at is not None
        assert ctx.aggregate_id == ""
        assert ctx.source_bc == ""
        assert ctx.event_type == ""

    def test_construction_with_values(self) -> None:
        eid = uuid4()
        causation = uuid4()
        ctx = EventContext(
            event_id=eid,
            correlation_id="corr-001",
            causation_id=causation,
            aggregate_id="agg-001",
            source_bc="ingestion",
            event_type="RawArticleCollected",
        )
        assert ctx.event_id == eid
        assert ctx.correlation_id == "corr-001"
        assert ctx.causation_id == causation
        assert ctx.aggregate_id == "agg-001"
        assert ctx.source_bc == "ingestion"
        assert ctx.event_type == "RawArticleCollected"

    def test_construction_generates_unique_event_ids(self) -> None:
        ctx_a = EventContext()
        ctx_b = EventContext()
        assert ctx_a.event_id != ctx_b.event_id

    def test_construction_generates_occurred_at(self) -> None:
        ctx = EventContext()
        assert ctx.occurred_at is not None
        assert ctx.occurred_at.tzinfo is not None


class TestEventContextImmutability:
    """Frozen dataclass behavior."""

    def test_frozen(self) -> None:
        ctx = EventContext()
        with pytest.raises(AttributeError):
            ctx.correlation_id = "changed"  # type: ignore[misc]

    def test_frozen_event_id(self) -> None:
        ctx = EventContext()
        with pytest.raises(AttributeError):
            ctx.event_id = uuid4()  # type: ignore[misc]

    def test_frozen_source_bc(self) -> None:
        ctx = EventContext()
        with pytest.raises(AttributeError):
            ctx.source_bc = "changed"  # type: ignore[misc]


class TestEventContextWithCausation:
    """with_causation creates derived context with causation set."""

    def test_with_causation(self) -> None:
        ctx = EventContext(
            correlation_id="corr-001",
            source_bc="ingestion",
            event_type="RawArticleCollected",
        )
        cause_id = uuid4()
        child = ctx.with_causation(cause_id)

        assert child.causation_id == cause_id
        # Preserves everything else
        assert child.event_id == ctx.event_id
        assert child.correlation_id == ctx.correlation_id
        assert child.occurred_at == ctx.occurred_at
        assert child.source_bc == ctx.source_bc
        assert child.event_type == ctx.event_type

    def test_with_causation_returns_new_object(self) -> None:
        ctx = EventContext(correlation_id="corr-001")
        child = ctx.with_causation(uuid4())
        assert child is not ctx

    def test_with_causation_original_unchanged(self) -> None:
        ctx = EventContext(correlation_id="corr-001")
        original_causation = ctx.causation_id
        ctx.with_causation(uuid4())
        assert ctx.causation_id == original_causation


class TestEventContextNewCorrelated:
    """new_correlated creates linked child context."""

    def test_new_correlated(self) -> None:
        ctx = EventContext(
            correlation_id="corr-001",
            source_bc="ingestion",
        )
        child = ctx.new_correlated("RecommendationGenerated", aggregate_id="agg-001")

        # New event_id
        assert child.event_id != ctx.event_id
        # Same correlation_id
        assert child.correlation_id == "corr-001"
        # Causation is parent's event_id
        assert child.causation_id == ctx.event_id
        # New fields
        assert child.event_type == "RecommendationGenerated"
        assert child.aggregate_id == "agg-001"
        # source_bc is always "learning"
        assert child.source_bc == "learning"

    def test_new_correlated_preserves_correlation_id(self) -> None:
        ctx = EventContext(correlation_id="same-corr")
        child = ctx.new_correlated("TestEvent")
        assert child.correlation_id == "same-corr"

    def test_new_correlated_generates_correlation_if_empty(self) -> None:
        ctx = EventContext(correlation_id="")
        child = ctx.new_correlated("TestEvent")
        # When correlation_id is empty, uses parent's event_id as correlation
        assert child.correlation_id == str(ctx.event_id)

    def test_new_correlated_with_aggregate_id(self) -> None:
        ctx = EventContext(correlation_id="corr-001")
        child = ctx.new_correlated("FeedbackRecorded", aggregate_id="fb-001")
        assert child.aggregate_id == "fb-001"

    def test_new_correlated_without_aggregate_id(self) -> None:
        ctx = EventContext(correlation_id="corr-001")
        child = ctx.new_correlated("DatasetReady")
        assert child.aggregate_id == ""


class TestEventContextChains:
    """Correlation and causation chains across multiple contexts."""

    def test_correlation_chain(self) -> None:
        root = EventContext(
            correlation_id="corr-001",
            source_bc="ingestion",
            event_type="RawArticleCollected",
        )
        step1 = root.new_correlated("RecommendationGenerated", aggregate_id="agg-1")
        step2 = step1.new_correlated("FeedbackRecorded", aggregate_id="agg-2")
        step3 = step2.new_correlated("DatasetReady", aggregate_id="agg-3")

        # All share the same correlation_id
        assert root.correlation_id == step1.correlation_id == step2.correlation_id == step3.correlation_id
        assert root.correlation_id == "corr-001"

    def test_causation_chain(self) -> None:
        root = EventContext(event_id=uuid4(), correlation_id="corr-001")
        step1 = root.new_correlated("RecommendationGenerated")
        step2 = step1.new_correlated("FeedbackRecorded")
        step3 = step2.new_correlated("DatasetReady")

        # Each step's causation points to the previous step's event_id
        assert step1.causation_id == root.event_id
        assert step2.causation_id == step1.event_id
        assert step3.causation_id == step2.event_id

    def test_chain_preserves_original_context(self) -> None:
        original_eid = uuid4()
        root = EventContext(event_id=original_eid, correlation_id="corr-001")
        child = root.new_correlated("RecommendationGenerated")
        grandchild = child.new_correlated("FeedbackRecorded")

        assert root.event_id == original_eid
        assert root.causation_id is None

    def test_with_causation_then_new_correlated(self) -> None:
        root = EventContext(correlation_id="corr-001")
        step1 = root.with_causation(uuid4())
        step2 = step1.new_correlated("TestEvent")

        assert step2.causation_id == step1.event_id
        assert step2.correlation_id == "corr-001"
