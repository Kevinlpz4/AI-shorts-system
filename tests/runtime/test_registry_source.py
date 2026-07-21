"""
Tests for SourceRegistry — build from config, get, list, filter.

Covers:
- Register and get sources
- Get all sources
- Get enabled sources only
- List by technology
- Get missing source returns None
"""
from __future__ import annotations

from runtime.contracts.source_definition import SourceDefinition
from runtime.registry.source_registry import SourceRegistry


class TestSourceRegistry:
    """Tests for SourceRegistry."""

    def test_empty_registry(self) -> None:
        """New registry has no sources."""
        registry = SourceRegistry()

        assert registry.get_all() == []
        assert registry.get("missing") is None

    def test_register_and_get(self) -> None:
        """Register a source and retrieve by id."""
        registry = SourceRegistry()
        source = SourceDefinition(id="src-1", provider="rss", technology="rss")

        registry.register(source)

        assert registry.get("src-1") is source

    def test_get_missing_returns_none(self) -> None:
        """Getting a nonexistent source returns None."""
        registry = SourceRegistry()

        assert registry.get("nonexistent") is None

    def test_get_all(self) -> None:
        """get_all returns all registered sources."""
        registry = SourceRegistry()
        s1 = SourceDefinition(id="s1", provider="p1", technology="rss")
        s2 = SourceDefinition(id="s2", provider="p2", technology="api")

        registry.register(s1)
        registry.register(s2)

        all_sources = registry.get_all()
        assert len(all_sources) == 2
        assert s1 in all_sources
        assert s2 in all_sources

    def test_get_enabled(self) -> None:
        """get_enabled returns only enabled sources."""
        registry = SourceRegistry()
        enabled = SourceDefinition(id="e1", provider="p", technology="rss", enabled=True)
        disabled = SourceDefinition(id="d1", provider="p", technology="rss", enabled=False)

        registry.register(enabled)
        registry.register(disabled)

        result = registry.get_enabled()
        assert len(result) == 1
        assert result[0].id == "e1"

    def test_list_by_technology(self) -> None:
        """list_by_technology filters by technology field."""
        registry = SourceRegistry()
        rss = SourceDefinition(id="r1", provider="p", technology="rss")
        api = SourceDefinition(id="a1", provider="p", technology="api")
        rss2 = SourceDefinition(id="r2", provider="p", technology="rss")

        registry.register(rss)
        registry.register(api)
        registry.register(rss2)

        rss_sources = registry.list_by_technology("rss")
        assert len(rss_sources) == 2
        assert all(s.technology == "rss" for s in rss_sources)

    def test_list_by_technology_empty(self) -> None:
        """list_by_technology returns empty list for unknown technology."""
        registry = SourceRegistry()
        registry.register(SourceDefinition(id="s1", provider="p", technology="rss"))

        assert registry.list_by_technology("graphql") == []

    def test_register_overwrites(self) -> None:
        """Registering same id overwrites previous source."""
        registry = SourceRegistry()
        original = SourceDefinition(id="s1", provider="p1", technology="rss")
        replacement = SourceDefinition(id="s1", provider="p2", technology="api")

        registry.register(original)
        registry.register(replacement)

        assert registry.get("s1") is replacement
        assert len(registry.get_all()) == 1
