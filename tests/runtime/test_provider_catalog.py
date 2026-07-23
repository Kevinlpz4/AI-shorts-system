"""
Tests for SourceDefinition Catalog — validates all providers are correctly defined.

Covers:
- All sources exist in catalog
- All sources have required fields
- Sources grouped by technology
- Lookup functions work correctly
"""
from __future__ import annotations

import pytest

from runtime.providers.catalog import (
    ALL_SOURCES,
    get_enabled_sources,
    get_source,
    get_sources_by_technology,
)


class TestProviderCatalog:
    """Tests for the SourceDefinition catalog."""

    def test_catalog_has_sources(self) -> None:
        """Catalog contains at least 8 sources."""
        assert len(ALL_SOURCES) >= 8

    def test_all_sources_have_required_fields(self) -> None:
        """Every source in catalog has id, provider, and technology."""
        for source in ALL_SOURCES:
            assert source.id, f"Source missing id: {source}"
            assert source.provider, f"Source '{source.id}' missing provider"
            assert source.technology, f"Source '{source.id}' missing technology"

    def test_no_duplicate_ids(self) -> None:
        """No two sources share the same id."""
        ids = [s.id for s in ALL_SOURCES]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {ids}"

    def test_rss_sources_exist(self) -> None:
        """At least 4 RSS sources are defined."""
        rss = get_sources_by_technology("rss")
        assert len(rss) >= 4

    def test_api_sources_exist(self) -> None:
        """At least 2 API sources are defined."""
        api = get_sources_by_technology("api")
        assert len(api) >= 2

    def test_reddit_sources_exist(self) -> None:
        """At least 1 Reddit source is defined."""
        reddit = get_sources_by_technology("reddit")
        assert len(reddit) >= 1

    def test_get_source_by_id(self) -> None:
        """get_source returns correct source by id."""
        source = get_source("google-news-ai")
        assert source is not None
        assert source.id == "google-news-ai"
        assert source.provider == "google-news"

    def test_get_source_missing(self) -> None:
        """get_source returns None for unknown id."""
        assert get_source("nonexistent") is None

    def test_get_enabled_sources(self) -> None:
        """get_enabled_sources returns only enabled sources."""
        enabled = get_enabled_sources()
        assert len(enabled) > 0
        assert all(s.enabled for s in enabled)

    def test_source_has_metadata_with_url(self) -> None:
        """RSS and API sources have 'url' or 'base_url' in metadata."""
        for source in ALL_SOURCES:
            if source.technology in ("rss", "api"):
                has_url = "url" in source.metadata or "base_url" in source.metadata
                assert has_url, f"Source '{source.id}' missing URL in metadata"

    def test_source_has_default_tags(self) -> None:
        """All sources have non-empty default_tags."""
        for source in ALL_SOURCES:
            assert source.default_tags, f"Source '{source.id}' missing default_tags"

    def test_google_news_config(self) -> None:
        """Google News source has correct configuration."""
        source = get_source("google-news-ai")
        assert source is not None
        assert source.technology == "rss"
        assert "ai" in source.categories
        assert source.metadata["url"].startswith("https://news.google.com")

    def test_hackernews_config(self) -> None:
        """Hacker News source has correct configuration."""
        source = get_source("hackernews")
        assert source is not None
        assert source.technology == "api"
        assert "base_url" in source.metadata

    def test_reddit_ai_config(self) -> None:
        """Reddit AI source has correct configuration."""
        source = get_source("reddit-ai")
        assert source is not None
        assert source.technology == "reddit"
        assert "artificial" in source.metadata["subreddits"]

    def test_github_trending_config(self) -> None:
        """GitHub trending source has correct configuration."""
        source = get_source("github-trending")
        assert source is not None
        assert source.technology == "api"
        assert "github.com" in source.metadata["base_url"]
