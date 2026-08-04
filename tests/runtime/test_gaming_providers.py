"""
Unit tests for Gaming Provider SourceDefinitions.

Validates:
- All gaming sources exist in catalog
- SourceDefinition fields are correctly set
- Sources have required metadata (url)
- No authentication required for any gaming provider
- Technology is correctly assigned
"""
from __future__ import annotations

from datetime import timedelta

from runtime.providers.catalog import ALL_SOURCES, get_source, get_sources_by_technology
from runtime.providers.rss.steam_news import STEAM_NEWS_SOURCE
from runtime.providers.rss.playstation_blog import PLAYSTATION_BLOG_SOURCE
from runtime.providers.rss.ign import IGN_SOURCE
from runtime.providers.rss.gamespot import GAMESPOT_SOURCE


# ── All gaming sources ──────────────────────────────────────────────

GAMING_SOURCES = [
    STEAM_NEWS_SOURCE,
    PLAYSTATION_BLOG_SOURCE,
    IGN_SOURCE,
    GAMESPOT_SOURCE,
]

GAMING_SOURCE_IDS = [
    "steam-news",
    "playstation-blog",
    "ign",
    "gamespot",
]


class TestGamingSourceDefinitions:
    """SourceDefinition structural validation for gaming providers."""

    def test_all_gaming_sources_in_catalog(self) -> None:
        """Every gaming source must be present in ALL_SOURCES."""
        catalog_ids = {s.id for s in ALL_SOURCES}
        for source_id in GAMING_SOURCE_IDS:
            assert source_id in catalog_ids, (
                f"Gaming source '{source_id}' missing from catalog"
            )

    def test_gaming_source_count(self) -> None:
        """Catalog must contain exactly 4 gaming sources."""
        gaming_in_catalog = [
            s for s in ALL_SOURCES
            if "gaming" in s.categories
        ]
        assert len(gaming_in_catalog) >= 4, (
            f"Expected at least 4 gaming sources, got {len(gaming_in_catalog)}"
        )

    def test_all_gaming_use_rss_technology(self) -> None:
        """All gaming providers use RSS technology."""
        for source in GAMING_SOURCES:
            assert source.technology == "rss", (
                f"{source.id}: expected technology='rss', got '{source.technology}'"
            )

    def test_all_gaming_use_rss_provider(self) -> None:
        """All gaming providers use RSS technology (provider is the real name)."""
        for source in GAMING_SOURCES:
            assert source.technology == "rss", (
                f"{source.id}: expected technology='rss', got '{source.technology}'"
            )

    def test_all_gaming_are_enabled(self) -> None:
        """All gaming providers must be enabled."""
        for source in GAMING_SOURCES:
            assert source.enabled is True, f"{source.id}: expected enabled=True"

    def test_all_gaming_have_gaming_category(self) -> None:
        """All gaming sources must include 'gaming' in categories."""
        for source in GAMING_SOURCES:
            assert "gaming" in source.categories, (
                f"{source.id}: expected 'gaming' in categories, got {source.categories}"
            )

    def test_all_gaming_have_url_metadata(self) -> None:
        """All gaming sources must have 'url' in metadata."""
        for source in GAMING_SOURCES:
            assert "url" in source.metadata, (
                f"{source.id}: expected 'url' in metadata"
            )
            assert source.metadata["url"].startswith("http"), (
                f"{source.id}: url metadata must be absolute URL"
            )

    def test_no_gaming_source_requires_auth(self) -> None:
        """Gaming RSS providers must not require authentication."""
        for source in GAMING_SOURCES:
            assert source.authentication is None, (
                f"{source.id}: gaming RSS should not require auth"
            )

    def test_all_gaming_have_retry_policy(self) -> None:
        """All gaming sources must have retry configuration."""
        for source in GAMING_SOURCES:
            assert source.retry_policy is not None, (
                f"{source.id}: expected retry_policy"
            )
            assert source.retry_policy.max_retries >= 2, (
                f"{source.id}: expected max_retries >= 2"
            )

    def test_all_gaming_have_rate_limit(self) -> None:
        """All gaming sources must have rate limiting."""
        for source in GAMING_SOURCES:
            assert source.rate_limit is not None, (
                f"{source.id}: expected rate_limit"
            )

    def test_all_gaming_have_poll_interval(self) -> None:
        """All gaming sources must have poll_interval."""
        for source in GAMING_SOURCES:
            assert source.poll_interval is not None, (
                f"{source.id}: expected poll_interval"
            )
            assert source.poll_interval >= timedelta(minutes=10), (
                f"{source.id}: poll_interval should be >= 10 minutes"
            )

    def test_all_gaming_have_default_tags(self) -> None:
        """All gaming sources must have default_tags."""
        for source in GAMING_SOURCES:
            assert len(source.default_tags) > 0, (
                f"{source.id}: expected non-empty default_tags"
            )


class TestGamingSourceLookup:
    """Catalog lookup helpers work for gaming sources."""

    def test_get_source_steam(self) -> None:
        source = get_source("steam-news")
        assert source is not None
        assert source.id == "steam-news"

    def test_get_source_playstation(self) -> None:
        source = get_source("playstation-blog")
        assert source is not None
        assert source.id == "playstation-blog"

    def test_get_source_ign(self) -> None:
        source = get_source("ign")
        assert source is not None
        assert source.id == "ign"

    def test_get_source_gamespot(self) -> None:
        source = get_source("gamespot")
        assert source is not None
        assert source.id == "gamespot"

    def test_get_sources_by_technology_rss_includes_gaming(self) -> None:
        rss_sources = get_sources_by_technology("rss")
        rss_ids = {s.id for s in rss_sources}
        for source_id in GAMING_SOURCE_IDS:
            assert source_id in rss_ids, (
                f"Gaming source '{source_id}' not found in RSS sources"
            )


class TestIndividualGamingSources:
    """Individual source definition validation."""

    def test_steam_news_metadata(self) -> None:
        assert STEAM_NEWS_SOURCE.id == "steam-news"
        assert STEAM_NEWS_SOURCE.metadata["url"] == "https://store.steampowered.com/feeds/news/"
        assert "pc" in STEAM_NEWS_SOURCE.categories

    def test_playstation_blog_metadata(self) -> None:
        assert PLAYSTATION_BLOG_SOURCE.id == "playstation-blog"
        assert PLAYSTATION_BLOG_SOURCE.metadata["url"] == "https://blog.playstation.com/feed/"
        assert "playstation" in PLAYSTATION_BLOG_SOURCE.categories

    def test_ign_metadata(self) -> None:
        assert IGN_SOURCE.id == "ign"
        assert IGN_SOURCE.metadata["url"] == "https://feeds.feedburner.com/ign/all"
        assert "gaming" in IGN_SOURCE.categories

    def test_gamespot_metadata(self) -> None:
        assert GAMESPOT_SOURCE.id == "gamespot"
        assert GAMESPOT_SOURCE.metadata["url"] == "https://www.gamespot.com/feeds/mashup/"
        assert "gaming" in GAMESPOT_SOURCE.categories
