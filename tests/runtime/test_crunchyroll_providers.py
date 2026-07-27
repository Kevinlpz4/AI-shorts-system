"""
Unit tests for Crunchyroll Provider SourceDefinitions.

Validates:
- Both Crunchyroll sources exist in catalog
- SourceDefinition fields are correctly set
- Sources have required metadata (url)
- No authentication required
- Technology is correctly assigned
- Categories match anime domain
"""
from __future__ import annotations

from datetime import timedelta

from runtime.contracts.source_definition import SourceDefinition
from runtime.providers.catalog import ALL_SOURCES, get_source, get_sources_by_technology
from runtime.providers.rss.crunchyroll_news import CRUNCHYROLL_NEWS_SOURCE
from runtime.providers.rss.crunchyroll_anime import CRUNCHYROLL_ANIME_SOURCE


# ── All Crunchyroll sources ──────────────────────────────────────────

CRUNCHYROLL_SOURCES = [
    CRUNCHYROLL_NEWS_SOURCE,
    CRUNCHYROLL_ANIME_SOURCE,
]

CRUNCHYROLL_SOURCE_IDS = [
    "crunchyroll-news",
    "crunchyroll-anime",
]


class TestCrunchyrollSourceDefinitions:
    """SourceDefinition structural validation for Crunchyroll providers."""

    def test_all_crunchyroll_sources_in_catalog(self) -> None:
        """Every Crunchyroll source must be present in ALL_SOURCES."""
        catalog_ids = {s.id for s in ALL_SOURCES}
        for source_id in CRUNCHYROLL_SOURCE_IDS:
            assert source_id in catalog_ids, (
                f"Crunchyroll source '{source_id}' missing from catalog"
            )

    def test_crunchyroll_source_count(self) -> None:
        """Catalog must contain exactly 2 Crunchyroll sources."""
        crunchyroll_in_catalog = [
            s for s in ALL_SOURCES
            if s.provider == "crunchyroll"
        ]
        assert len(crunchyroll_in_catalog) == 2, (
            f"Expected 2 Crunchyroll sources, got {len(crunchyroll_in_catalog)}"
        )

    def test_all_crunchyroll_use_rss_technology(self) -> None:
        """All Crunchyroll providers use RSS technology."""
        for source in CRUNCHYROLL_SOURCES:
            assert source.technology == "rss", (
                f"{source.id}: expected technology='rss', got '{source.technology}'"
            )

    def test_all_crunchyroll_are_enabled(self) -> None:
        """All Crunchyroll providers must be enabled."""
        for source in CRUNCHYROLL_SOURCES:
            assert source.enabled is True, f"{source.id}: expected enabled=True"

    def test_all_crunchyroll_have_anime_category(self) -> None:
        """All Crunchyroll sources must include 'anime' in categories."""
        for source in CRUNCHYROLL_SOURCES:
            assert "anime" in source.categories, (
                f"{source.id}: expected 'anime' in categories, got {source.categories}"
            )

    def test_all_crunchyroll_have_url_metadata(self) -> None:
        """All Crunchyroll sources must have 'url' in metadata."""
        for source in CRUNCHYROLL_SOURCES:
            assert "url" in source.metadata, (
                f"{source.id}: expected 'url' in metadata"
            )
            assert source.metadata["url"].startswith("http"), (
                f"{source.id}: url metadata must be absolute URL"
            )

    def test_no_crunchyroll_source_requires_auth(self) -> None:
        """Crunchyroll RSS providers must not require authentication."""
        for source in CRUNCHYROLL_SOURCES:
            assert source.authentication is None, (
                f"{source.id}: Crunchyroll RSS should not require auth"
            )

    def test_all_crunchyroll_have_retry_policy(self) -> None:
        """All Crunchyroll sources must have retry configuration."""
        for source in CRUNCHYROLL_SOURCES:
            assert source.retry_policy is not None, (
                f"{source.id}: expected retry_policy"
            )
            assert source.retry_policy.max_retries >= 2, (
                f"{source.id}: expected max_retries >= 2"
            )

    def test_all_crunchyroll_have_rate_limit(self) -> None:
        """All Crunchyroll sources must have rate limiting."""
        for source in CRUNCHYROLL_SOURCES:
            assert source.rate_limit is not None, (
                f"{source.id}: expected rate_limit"
            )

    def test_all_crunchyroll_have_poll_interval(self) -> None:
        """All Crunchyroll sources must have poll_interval."""
        for source in CRUNCHYROLL_SOURCES:
            assert source.poll_interval is not None, (
                f"{source.id}: expected poll_interval"
            )
            assert source.poll_interval >= timedelta(minutes=10), (
                f"{source.id}: poll_interval should be >= 10 minutes"
            )

    def test_all_crunchyroll_have_default_tags(self) -> None:
        """All Crunchyroll sources must have default_tags."""
        for source in CRUNCHYROLL_SOURCES:
            assert len(source.default_tags) > 0, (
                f"{source.id}: expected non-empty default_tags"
            )

    def test_all_crunchyroll_have_crunchyroll_tag(self) -> None:
        """All Crunchyroll sources must include 'crunchyroll' in default_tags."""
        for source in CRUNCHYROLL_SOURCES:
            assert "crunchyroll" in source.default_tags, (
                f"{source.id}: expected 'crunchyroll' in default_tags"
            )


class TestCrunchyrollSourceLookup:
    """Catalog lookup helpers work for Crunchyroll sources."""

    def test_get_source_crunchyroll_news(self) -> None:
        source = get_source("crunchyroll-news")
        assert source is not None
        assert source.id == "crunchyroll-news"

    def test_get_source_crunchyroll_anime(self) -> None:
        source = get_source("crunchyroll-anime")
        assert source is not None
        assert source.id == "crunchyroll-anime"

    def test_get_sources_by_technology_rss_includes_crunchyroll(self) -> None:
        rss_sources = get_sources_by_technology("rss")
        rss_ids = {s.id for s in rss_sources}
        for source_id in CRUNCHYROLL_SOURCE_IDS:
            assert source_id in rss_ids, (
                f"Crunchyroll source '{source_id}' not found in RSS sources"
            )


class TestIndividualCrunchyrollSources:
    """Individual source definition validation."""

    def test_crunchyroll_news_metadata(self) -> None:
        assert CRUNCHYROLL_NEWS_SOURCE.id == "crunchyroll-news"
        assert CRUNCHYROLL_NEWS_SOURCE.provider == "crunchyroll"
        assert CRUNCHYROLL_NEWS_SOURCE.metadata["url"] == (
            "https://cr-news-api-service.prd.crunchyrollsvc.com/v1/en-US/rss"
        )
        assert "anime" in CRUNCHYROLL_NEWS_SOURCE.categories
        assert "news" in CRUNCHYROLL_NEWS_SOURCE.categories

    def test_crunchyroll_anime_metadata(self) -> None:
        assert CRUNCHYROLL_ANIME_SOURCE.id == "crunchyroll-anime"
        assert CRUNCHYROLL_ANIME_SOURCE.provider == "crunchyroll"
        assert CRUNCHYROLL_ANIME_SOURCE.metadata["url"] == (
            "http://feeds.feedburner.com/crunchyroll/rss/anime"
        )
        assert "anime" in CRUNCHYROLL_ANIME_SOURCE.categories
        assert "episodes" in CRUNCHYROLL_ANIME_SOURCE.categories

    def test_both_share_provider(self) -> None:
        """Both sources share the same provider identifier."""
        assert CRUNCHYROLL_NEWS_SOURCE.provider == CRUNCHYROLL_ANIME_SOURCE.provider
        assert CRUNCHYROLL_NEWS_SOURCE.provider == "crunchyroll"

    def test_different_categories(self) -> None:
        """News focuses on news, Anime focuses on episodes."""
        assert "news" in CRUNCHYROLL_NEWS_SOURCE.categories
        assert "episodes" in CRUNCHYROLL_ANIME_SOURCE.categories
        assert "episodes" not in CRUNCHYROLL_NEWS_SOURCE.categories
        assert "news" not in CRUNCHYROLL_ANIME_SOURCE.categories
