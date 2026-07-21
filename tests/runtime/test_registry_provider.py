"""
Tests for ProviderRegistry — register, get, list.

Covers:
- Register and get providers
- Get all providers
- List names
- Get missing provider returns None
- Register overwrites
"""
from __future__ import annotations

from typing import Any

import pytest

from runtime.registry.provider_registry import ProviderAdapter, ProviderRegistry


class FakeProvider:
    """Minimal fake provider that satisfies ProviderAdapter protocol."""

    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def fetch(self, source_id: str, config: dict[str, Any]) -> list[dict[str, str]]:
        return [{"title": f"from-{self._name}"}]


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def test_empty_registry(self) -> None:
        """New registry has no providers."""
        registry = ProviderRegistry()

        assert registry.get_all() == []
        assert registry.list_names() == []
        assert registry.get("missing") is None

    def test_register_and_get(self) -> None:
        """Register a provider and retrieve by name."""
        registry = ProviderRegistry()
        provider = FakeProvider("rss")

        registry.register(provider)

        assert registry.get("rss") is provider

    def test_get_missing_returns_none(self) -> None:
        """Getting a nonexistent provider returns None."""
        registry = ProviderRegistry()

        assert registry.get("nonexistent") is None

    def test_get_all(self) -> None:
        """get_all returns all registered providers."""
        registry = ProviderRegistry()
        p1 = FakeProvider("rss")
        p2 = FakeProvider("api")

        registry.register(p1)
        registry.register(p2)

        all_providers = registry.get_all()
        assert len(all_providers) == 2
        assert p1 in all_providers
        assert p2 in all_providers

    def test_list_names(self) -> None:
        """list_names returns all provider names."""
        registry = ProviderRegistry()
        registry.register(FakeProvider("rss"))
        registry.register(FakeProvider("api"))

        names = registry.list_names()
        assert set(names) == {"rss", "api"}

    def test_register_overwrites(self) -> None:
        """Registering same name overwrites previous provider."""
        registry = ProviderRegistry()
        original = FakeProvider("rss")
        replacement = FakeProvider("rss")

        registry.register(original)
        registry.register(replacement)

        assert registry.get("rss") is replacement
        assert len(registry.get_all()) == 1
