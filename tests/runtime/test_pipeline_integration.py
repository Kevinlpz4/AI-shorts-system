"""
Tests for full pipeline integration — Ingest → Normalize → Deduplicate.

Uses mocked adapters to verify the full pipeline flow.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.contracts.job_result import JobContext
from runtime.contracts.source_definition import SourceDefinition
from runtime.event_bridge import EventBridge
from runtime.jobs.ingestion_job import IngestionJob
from runtime.pipelines.deduplicate_step import DeduplicateStep
from runtime.pipelines.ingest_step import IngestStep
from runtime.pipelines.normalize_step import NormalizeStep
from runtime.registry.provider_registry import ProviderRegistry
from runtime.registry.source_registry import SourceRegistry
from runtime.registry.step_registry import StepRegistry


def _build_pipeline(
    source_items: dict[str, list[dict[str, str]]] | None = None,
) -> IngestionJob:
    """Build a complete pipeline with mocked providers."""
    source_reg = SourceRegistry()
    provider_reg = ProviderRegistry()
    step_reg = StepRegistry()

    if source_items is None:
        source_items = {}

    for source_id, items in source_items.items():
        source_reg.register(
            SourceDefinition(
                id=source_id,
                provider="mock",
                technology="mock",
                metadata={"url": "https://mock.test"},
            )
        )

    mock_provider = MagicMock()
    mock_provider.name = "mock"

    async def mock_fetch(source_id, config):
        return source_items.get(source_id, [])

    mock_provider.fetch = mock_fetch
    provider_reg.register(mock_provider)

    ingest = IngestStep(source_reg, provider_reg)
    normalize = NormalizeStep()
    dedup = DeduplicateStep()

    step_reg.register(ingest)
    step_reg.register(normalize)
    step_reg.register(dedup)

    return IngestionJob(step_reg)


class TestPipelineIntegration:
    """Integration tests for the full ingestion pipeline."""

    @pytest.mark.asyncio
    async def test_empty_pipeline(self) -> None:
        """Pipeline with no sources completes successfully."""
        job = _build_pipeline({})
        ctx = JobContext()

        result = await job.execute(ctx)

        assert result.is_success
        job_result = result.unwrap()
        assert job_result.success is True
        assert job_result.pipeline_result.total_items_output == 0

    @pytest.mark.asyncio
    async def test_single_source_pipeline(self) -> None:
        """Pipeline with one source processes items end-to-end."""
        job = _build_pipeline({
            "src1": [
                {"title": "Article 1", "url": "https://a.com/1", "source_id": "src1", "content_hash": "h1"},
                {"title": "Article 2", "url": "https://a.com/2", "source_id": "src1", "content_hash": "h2"},
            ],
        })
        ctx = JobContext()

        result = await job.execute(ctx)

        assert result.is_success
        job_result = result.unwrap()
        assert job_result.success is True
        # Pipeline has 3 steps; total_items_output is sum across all steps
        assert len(job_result.pipeline_result.steps) == 3
        # The last step (deduplicate) outputs 2 unique items
        dedup_step = job_result.pipeline_result.steps[2]
        assert dedup_step.items_output == 2

    @pytest.mark.asyncio
    async def test_multi_source_with_duplicates(self) -> None:
        """Pipeline deduplicates across sources."""
        job = _build_pipeline({
            "src1": [
                {"title": "Article 1", "url": "https://a.com/1", "source_id": "src1", "content_hash": "shared_hash"},
                {"title": "Article 2", "url": "https://a.com/2", "source_id": "src1", "content_hash": "unique_hash"},
            ],
            "src2": [
                {"title": "Article 1 dup", "url": "https://a.com/1", "source_id": "src2", "content_hash": "shared_hash"},
                {"title": "Article 3", "url": "https://a.com/3", "source_id": "src2", "content_hash": "hash3"},
            ],
        })
        ctx = JobContext()

        result = await job.execute(ctx)

        assert result.is_success
        job_result = result.unwrap()
        # After dedup: 3 unique items (shared_hash deduplicated once)
        dedup_step = job_result.pipeline_result.steps[2]
        assert dedup_step.items_output == 3

    @pytest.mark.asyncio
    async def test_pipeline_events_published(self) -> None:
        """Pipeline publishes events through EventBridge."""
        bridge = EventBridge()
        source_reg = SourceRegistry()
        provider_reg = ProviderRegistry()
        step_reg = StepRegistry()

        source_reg.register(
            SourceDefinition(id="s", provider="m", technology="m", metadata={})
        )
        mock_provider = MagicMock()
        mock_provider.name = "m"
        mock_provider.fetch = AsyncMock(return_value=[])
        provider_reg.register(mock_provider)

        step_reg.register(IngestStep(source_reg, provider_reg))
        step_reg.register(NormalizeStep())
        step_reg.register(DeduplicateStep())

        job = IngestionJob(step_reg, event_bridge=bridge)
        ctx = JobContext()

        await job.execute(ctx)

        events = bridge.drain()
        event_types = [e.event_type for e in events]
        # Both orchestrator and job emit events
        assert "pipeline.completed" in event_types
        assert "ingestion.completed" in event_types
