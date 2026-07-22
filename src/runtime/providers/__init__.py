"""
External knowledge providers — TechnologyAdapters and ProviderAdapters.

This package implements the provider architecture from EPIC 8.1:

- **TechnologyAdapters**: Generic fetchers for each technology type
  (RSS, REST API, Reddit RSS). One adapter per technology.

- **ProviderAdapters**: Thin configuration layers on top of a
  TechnologyAdapter. One per source (Google News, HN, etc.).

- **Catalog**: Declarative SourceDefinition catalog for all providers.

Usage::

    from runtime.providers.catalog import ALL_SOURCES
    from runtime.providers.rss.rss_provider import RSSProvider
"""
from __future__ import annotations
