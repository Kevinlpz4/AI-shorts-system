"""
Tests for NormalizeStep — normalization pipeline step.

Covers:
- Normalizes provider results correctly
- Skips items without title or url
- Stores normalized items in PipelineContext
- Handles empty input
"""
from __future__ import annotations

import pytest

from foundation.result.result import Result
from runtime.contracts.pipeline_context import PipelineContext
from runtime.contracts.provider_result import ProviderResult
from runtime.pipelines.normalize_step import NormalizeStep


class TestNormalizeStep:
    """Tests for NormalizeStep pipeline step."""

    def test_name_and_order(self) -> None:
        """NormalizeStep has correct name and order."""
        step = NormalizeStep()
        assert step.name == "normalize"
        assert step.order == 2

    @pytest.mark.asyncio
    async def test_no_input(self) -> None:
        """NormalizeStep succeeds with no input from ingest step."""
        step = NormalizeStep()
        ctx = PipelineContext()

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_output == 0

    @pytest.mark.asyncio
    async def test_normalizes_items(self) -> None:
        """NormalizeStep normalizes raw items to standard format."""
        step = NormalizeStep()
        ctx = PipelineContext()

        provider_result = ProviderResult(
            source_id="test",
            provider="rss",
            items=[
                {"title": "Article 1", "url": "https://example.com/1", "source_id": "test"},
                {"title": "Article 2", "url": "https://example.com/2", "source_id": "test"},
            ],
        )
        ctx.set_step_result("ingest", [provider_result])

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_output == 2

        normalized = ctx.get_step_result("normalize")
        assert len(normalized) == 2
        assert normalized[0]["title"] == "Article 1"
        assert "normalized_at" in normalized[0]

    @pytest.mark.asyncio
    async def test_skips_empty_items(self) -> None:
        """NormalizeStep skips items without title or url."""
        step = NormalizeStep()
        ctx = PipelineContext()

        provider_result = ProviderResult(
            source_id="test",
            provider="rss",
            items=[
                {"title": "Good", "url": "https://example.com/good"},
                {"title": "", "url": ""},  # Should be skipped
                {"title": "Also Good", "url": "https://example.com/also"},
            ],
        )
        ctx.set_step_result("ingest", [provider_result])

        result = await step.execute(ctx)

        assert result.is_success
        normalized = ctx.get_step_result("normalize")
        assert len(normalized) == 2

    @pytest.mark.asyncio
    async def test_carry_forward_extra_fields(self) -> None:
        """NormalizeStep carries forward provider-specific fields."""
        step = NormalizeStep()
        ctx = PipelineContext()

        provider_result = ProviderResult(
            source_id="test",
            provider="reddit",
            items=[
                {
                    "title": "Post",
                    "url": "https://reddit.com/1",
                    "subreddit": "artificial",
                    "content_hash": "abc123",
                },
            ],
        )
        ctx.set_step_result("ingest", [provider_result])

        result = await step.execute(ctx)

        normalized = ctx.get_step_result("normalize")
        assert normalized[0]["subreddit"] == "artificial"
        assert normalized[0]["content_hash"] == "abc123"

    @pytest.mark.asyncio
    async def test_preserves_errors_from_provider(self) -> None:
        """NormalizeStep preserves error messages from provider results."""
        step = NormalizeStep()
        ctx = PipelineContext()

        provider_result = ProviderResult(
            source_id="test",
            provider="rss",
            items=[],
            errors=["Connection timeout"],
        )
        ctx.set_step_result("ingest", [provider_result])

        result = await step.execute(ctx)

        step_result = result.unwrap()
        assert "Connection timeout" in step_result.errors
