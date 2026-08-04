"""
Tests for IngestStep — ingestion pipeline step.

Covers:
- Fetches from all enabled sources
- Handles provider not found gracefully
- Handles fetch errors gracefully
- Stores results in PipelineContext
- Empty source list
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.source_definition import SourceDefinition
from runtime.pipelines.ingest_step import IngestStep
from runtime.registry.provider_registry import ProviderRegistry
from runtime.registry.source_registry import SourceRegistry


def _make_source(
    source_id: str = "test-source",
    provider: str = "rss",
    technology: str = "rss",
    enabled: bool = True,
    metadata: dict | None = None,
) -> SourceDefinition:
    return SourceDefinition(
        id=source_id,
        provider=provider,
        technology=technology,
        enabled=enabled,
        metadata=metadata or {"url": "https://example.com/feed.xml"},
    )


class TestIngestStep:
    """Tests for IngestStep pipeline step."""

    def test_name_and_order(self) -> None:
        """IngestStep has correct name and order."""
        step = IngestStep(SourceRegistry(), ProviderRegistry())
        assert step.name == "ingest"
        assert step.order == 1
        assert step.is_fatal is False

    @pytest.mark.asyncio
    async def test_no_enabled_sources(self) -> None:
        """IngestStep succeeds with zero sources."""
        step = IngestStep(SourceRegistry(), ProviderRegistry())
        ctx = PipelineContext()

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_output == 0

    @pytest.mark.asyncio
    async def test_fetches_from_sources(self) -> None:
        """IngestStep fetches items from all enabled sources."""
        source_reg = SourceRegistry()
        provider_reg = ProviderRegistry()

        source = _make_source()
        source_reg.register(source)

        mock_provider = MagicMock()
        mock_provider.name = "rss"
        mock_provider.fetch = AsyncMock(
            return_value=[{"title": "T", "url": "https://x.com"}]
        )
        provider_reg.register(mock_provider)

        step = IngestStep(source_reg, provider_reg)
        ctx = PipelineContext()

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_output == 1

        # Verify context has results
        stored = ctx.get_step_result("ingest")
        assert stored is not None
        assert len(stored) == 1

    @pytest.mark.asyncio
    async def test_provider_not_found(self) -> None:
        """IngestStep handles missing provider gracefully."""
        source_reg = SourceRegistry()
        provider_reg = ProviderRegistry()

        source = _make_source(provider="unknown")
        source_reg.register(source)

        step = IngestStep(source_reg, provider_reg)
        ctx = PipelineContext()

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_output == 0
        assert len(step_result.errors) > 0

    @pytest.mark.asyncio
    async def test_fetch_error_continues(self) -> None:
        """IngestStep continues after one source fails."""
        source_reg = SourceRegistry()
        provider_reg = ProviderRegistry()

        source1 = _make_source(source_id="good")
        source2 = _make_source(source_id="bad", provider="rss")
        source_reg.register(source1)
        source_reg.register(source2)

        good_provider = MagicMock()
        good_provider.name = "rss"
        good_provider.fetch = AsyncMock(
            return_value=[{"title": "OK", "url": "https://ok.com"}]
        )
        provider_reg.register(good_provider)

        step = IngestStep(source_reg, provider_reg)
        ctx = PipelineContext()

        # Patch the fetch for 'bad' source to raise
        original_fetch = step._fetch_source

        async def patched_fetch(source):
            if source.id == "bad":
                raise ConnectionError("Network down")
            return await original_fetch(source)

        step._fetch_source = patched_fetch

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_output == 1
