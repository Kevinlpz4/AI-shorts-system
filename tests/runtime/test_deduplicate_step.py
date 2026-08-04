"""
Tests for DeduplicateStep — deduplication pipeline step.

Covers:
- Exact duplicate removal by content_hash
- Near-duplicate removal by URL normalization
- No duplicates case
- Empty input
"""
from __future__ import annotations

import pytest

from runtime.contracts.pipeline_context import PipelineContext
from runtime.pipelines.deduplicate_step import DeduplicateStep


class TestDeduplicateStep:
    """Tests for DeduplicateStep pipeline step."""

    def test_name_and_order(self) -> None:
        """DeduplicateStep has correct name and order."""
        step = DeduplicateStep()
        assert step.name == "deduplicate"
        assert step.order == 3

    @pytest.mark.asyncio
    async def test_no_input(self) -> None:
        """DeduplicateStep succeeds with no normalized items."""
        step = DeduplicateStep()
        ctx = PipelineContext()

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_output == 0

    @pytest.mark.asyncio
    async def test_no_duplicates(self) -> None:
        """DeduplicateStep keeps all unique items."""
        step = DeduplicateStep()
        ctx = PipelineContext()

        items = [
            {"title": "A", "url": "https://a.com", "content_hash": "hash_a"},
            {"title": "B", "url": "https://b.com", "content_hash": "hash_b"},
            {"title": "C", "url": "https://c.com", "content_hash": "hash_c"},
        ]
        ctx.set_step_result("normalize", items)

        result = await step.execute(ctx)

        assert result.is_success
        step_result = result.unwrap()
        assert step_result.items_output == 3

        deduplicated = ctx.get_step_result("deduplicate")
        assert len(deduplicated) == 3

    @pytest.mark.asyncio
    async def test_exact_duplicates_removed(self) -> None:
        """DeduplicateStep removes items with same content_hash."""
        step = DeduplicateStep()
        ctx = PipelineContext()

        items = [
            {"title": "A v1", "url": "https://a.com/1", "content_hash": "same_hash"},
            {"title": "A v2", "url": "https://a.com/2", "content_hash": "same_hash"},
            {"title": "B", "url": "https://b.com", "content_hash": "hash_b"},
        ]
        ctx.set_step_result("normalize", items)

        result = await step.execute(ctx)

        assert result.is_success
        deduplicated = ctx.get_step_result("deduplicate")
        assert len(deduplicated) == 2

    @pytest.mark.asyncio
    async def test_near_duplicates_by_url(self) -> None:
        """DeduplicateStep removes near-duplicates with similar URLs."""
        step = DeduplicateStep()
        ctx = PipelineContext()

        items = [
            {"title": "A", "url": "https://www.example.com/article", "content_hash": "h1"},
            {"title": "A dup", "url": "https://example.com/article", "content_hash": "h2"},
            {"title": "A dup2", "url": "https://example.com/article/", "content_hash": "h3"},
        ]
        ctx.set_step_result("normalize", items)

        await step.execute(ctx)

        deduplicated = ctx.get_step_result("deduplicate")
        # www. prefix and trailing slash are normalized
        assert len(deduplicated) == 1

    @pytest.mark.asyncio
    async def test_different_urls_kept(self) -> None:
        """DeduplicateStep keeps items with different URLs."""
        step = DeduplicateStep()
        ctx = PipelineContext()

        items = [
            {"title": "A", "url": "https://a.com/article-1", "content_hash": "h1"},
            {"title": "B", "url": "https://a.com/article-2", "content_hash": "h2"},
        ]
        ctx.set_step_result("normalize", items)

        await step.execute(ctx)

        deduplicated = ctx.get_step_result("deduplicate")
        assert len(deduplicated) == 2

    def test_url_normalization(self) -> None:
        """DeduplicateStep normalizes URLs correctly."""
        step = DeduplicateStep()

        assert step._normalize_url("https://www.example.com/path/") == "https://example.com/path"
        assert step._normalize_url("HTTP://EXAMPLE.COM/Path") == "http://example.com/Path"
        assert step._normalize_url("") == ""
        # Non-URL strings are returned lowercased
        result = step._normalize_url("not-a-url")
        assert isinstance(result, str)
