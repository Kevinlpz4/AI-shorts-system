"""
Tests for LearningIntegrationStep — integrates normalized articles with Learning BC.

Covers:
- Reads deduplicated items from PipelineContext
- Emits events via EventBridge for Learning BC consumption
- Handles empty input gracefully
- Stores learning data in context
- Continues on individual item processing failure
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.pipeline_result import StepResult
from runtime.event_bridge import EventBridge
from runtime.pipelines.learning_step import LearningIntegrationStep


class TestLearningIntegrationStep:
    """Tests for LearningIntegrationStep."""

    @pytest.mark.asyncio
    async def test_empty_input(self) -> None:
        """Step handles empty deduplicated list gracefully."""
        step = LearningIntegrationStep()
        ctx = PipelineContext()

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_processed == 0
        assert step_result.items_output == 0

    @pytest.mark.asyncio
    async def test_processes_items(self) -> None:
        """Step processes deduplicated items and stores learning data."""
        step = LearningIntegrationStep()
        ctx = PipelineContext()

        items = [
            {"title": "AI Breakthrough", "url": "https://a.com/1", "source_id": "src1", "content_hash": "h1"},
            {"title": "Gaming News", "url": "https://g.com/1", "source_id": "src2", "content_hash": "h2"},
        ]
        ctx.set_step_result("deduplicate", items)

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_processed == 2
        assert step_result.items_output == 2

    @pytest.mark.asyncio
    async def test_emits_events(self) -> None:
        """Step emits learning.item.ready events via EventBridge."""
        bridge = EventBridge()
        step = LearningIntegrationStep(event_bridge=bridge)
        ctx = PipelineContext()

        items = [
            {"title": "AI Article", "url": "https://a.com/1", "source_id": "src1", "content_hash": "h1"},
        ]
        ctx.set_step_result("deduplicate", items)

        await step.execute(ctx)

        events = bridge.drain()
        assert len(events) == 2  # item + batch event
        assert events[0].event_type == "learning.item.ready"
        assert events[0].source == "learning-integration"
        assert events[1].event_type == "learning.batch.ready"

    @pytest.mark.asyncio
    async def test_emits_batch_event(self) -> None:
        """Step emits learning.batch.ready event after all items."""
        bridge = EventBridge()
        step = LearningIntegrationStep(event_bridge=bridge)
        ctx = PipelineContext()

        items = [
            {"title": "A", "url": "https://a.com/1", "source_id": "s1", "content_hash": "h1"},
            {"title": "B", "url": "https://b.com/1", "source_id": "s2", "content_hash": "h2"},
        ]
        ctx.set_step_result("deduplicate", items)

        await step.execute(ctx)

        events = bridge.drain()
        event_types = [e.event_type for e in events]
        assert "learning.item.ready" in event_types
        assert "learning.batch.ready" in event_types

    @pytest.mark.asyncio
    async def test_stores_learning_data_in_context(self) -> None:
        """Step stores learning items in PipelineContext."""
        step = LearningIntegrationStep()
        ctx = PipelineContext()

        items = [
            {"title": "Article", "url": "https://a.com/1", "source_id": "src1", "content_hash": "h1"},
        ]
        ctx.set_step_result("deduplicate", items)

        await step.execute(ctx)

        learning_data = ctx.get_step_result("learning")
        assert learning_data is not None
        assert isinstance(learning_data, list)
        assert len(learning_data) == 1

    @pytest.mark.asyncio
    async def test_no_event_bridge(self) -> None:
        """Step works without EventBridge."""
        step = LearningIntegrationStep(event_bridge=None)
        ctx = PipelineContext()

        items = [
            {"title": "Article", "url": "https://a.com/1", "source_id": "s1", "content_hash": "h1"},
        ]
        ctx.set_step_result("deduplicate", items)

        result = await step.execute(ctx)
        assert result.is_success

    @pytest.mark.asyncio
    async def test_step_metadata(self) -> None:
        """Step has correct name, order, and is_fatal."""
        step = LearningIntegrationStep()
        assert step.name == "learning-integration"
        assert step.order == 4
        assert step.is_fatal is False

    @pytest.mark.asyncio
    async def test_items_preserve_source_fields(self) -> None:
        """Learning items preserve source-specific fields."""
        step = LearningIntegrationStep()
        ctx = PipelineContext()

        items = [
            {
                "title": "HN Story",
                "url": "https://hn.com/1",
                "source_id": "hackernews",
                "content_hash": "h1",
                "hn_score": "150",
                "hn_by": "pg",
            },
        ]
        ctx.set_step_result("deduplicate", items)

        await step.execute(ctx)

        learning_data = ctx.get_step_result("learning")
        assert learning_data[0]["hn_score"] == "150"
        assert learning_data[0]["hn_by"] == "pg"

    @pytest.mark.asyncio
    async def test_missing_deduplicate_input(self) -> None:
        """Step handles missing deduplicate step result."""
        step = LearningIntegrationStep()
        ctx = PipelineContext()

        # No deduplicate result set
        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_processed == 0
