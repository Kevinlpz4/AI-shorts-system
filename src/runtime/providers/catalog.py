"""
SourceDefinition Catalog — declarative configuration for ALL providers.

Every external knowledge source is defined as a SourceDefinition.
Adding a new source of the same technology = 1 SourceDefinition + 0 new code.

Usage::

    from runtime.providers.catalog import ALL_SOURCES, get_sources_by_technology

    rss_sources = get_sources_by_technology("rss")
    all_sources = ALL_SOURCES
"""
from __future__ import annotations

from runtime.contracts.source_definition import SourceDefinition
from runtime.providers.api.github import GITHUB_TRENDING_SOURCE
from runtime.providers.api.hackernews import HACKERNEWS_SOURCE
from runtime.providers.rss.anthropic import ANTHROPIC_SOURCE
from runtime.providers.rss.devto import DEVTO_SOURCE
from runtime.providers.rss.gamespot import GAMESPOT_SOURCE
from runtime.providers.rss.google_news import GOOGLE_NEWS_SOURCE
from runtime.providers.rss.ign import IGN_SOURCE
from runtime.providers.rss.openai_blog import OPENAI_BLOG_SOURCE
from runtime.providers.rss.playstation_blog import PLAYSTATION_BLOG_SOURCE
from runtime.providers.rss.crunchyroll_anime import CRUNCHYROLL_ANIME_SOURCE
from runtime.providers.rss.crunchyroll_news import CRUNCHYROLL_NEWS_SOURCE
from runtime.providers.rss.steam_news import STEAM_NEWS_SOURCE
from runtime.providers.rss.techcrunch import TECHCRUNCH_SOURCE
from runtime.providers.rss.theverge import THEVERGE_SOURCE
from runtime.providers.reddit.reddit_ai import REDDIT_AI_SOURCE
from runtime.providers.reddit.reddit_gaming import REDDIT_GAMING_SOURCE

# ── All sources in catalog ──────────────────────────────────────────
ALL_SOURCES: list[SourceDefinition] = [
    # RSS Sources — Tech (6)
    GOOGLE_NEWS_SOURCE,
    OPENAI_BLOG_SOURCE,
    ANTHROPIC_SOURCE,
    TECHCRUNCH_SOURCE,
    THEVERGE_SOURCE,
    DEVTO_SOURCE,
    # RSS Sources — Gaming (4)
    STEAM_NEWS_SOURCE,
    PLAYSTATION_BLOG_SOURCE,
    IGN_SOURCE,
    GAMESPOT_SOURCE,
    # RSS Sources — Anime (2)
    CRUNCHYROLL_NEWS_SOURCE,
    CRUNCHYROLL_ANIME_SOURCE,
    # Reddit Sources (2)
    REDDIT_AI_SOURCE,
    REDDIT_GAMING_SOURCE,
    # API Sources (2)
    HACKERNEWS_SOURCE,
    GITHUB_TRENDING_SOURCE,
]

# ── Lookup helpers ──────────────────────────────────────────────────

_SOURCES_BY_ID: dict[str, SourceDefinition] = {s.id: s for s in ALL_SOURCES}
_SOURCES_BY_TECH: dict[str, list[SourceDefinition]] = {}
for _s in ALL_SOURCES:
    _SOURCES_BY_TECH.setdefault(_s.technology, []).append(_s)


def get_source(source_id: str) -> SourceDefinition | None:
    """Get a source by id from the catalog."""
    return _SOURCES_BY_ID.get(source_id)


def get_sources_by_technology(technology: str) -> list[SourceDefinition]:
    """Get all sources for a technology type (rss, api, reddit)."""
    return list(_SOURCES_BY_TECH.get(technology, []))


def get_enabled_sources() -> list[SourceDefinition]:
    """Get all enabled sources from the catalog."""
    return [s for s in ALL_SOURCES if s.enabled]
