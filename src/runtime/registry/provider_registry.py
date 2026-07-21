"""
ProviderRegistry — manages provider adapter instances.

Providers are registered by name and can be retrieved for fetching
data from sources.

Usage::

    from runtime.registry.provider_registry import ProviderRegistry

    registry = ProviderRegistry()
    registry.register(rss_adapter)
    adapter = registry.get("rss")
"""
from __future__ import annotations

from typing import Any, Protocol


class ProviderAdapter(Protocol):
    """Protocol for provider adapters that fetch data from sources.

    A provider adapter knows how to fetch data from a specific technology
    (RSS, API, GraphQL, etc.). Each technology provides ONE adapter class.
    """

    @property
    def name(self) -> str:
        """Unique name for this provider (e.g., ``'rss'``, ``'newsapi'``)."""
        ...

    async def fetch(
        self, source_id: str, config: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Fetch data from the given source.

        Args:
            source_id: The source identifier to fetch from.
            config: Provider-specific configuration.

        Returns:
            List of raw items as dicts.
        """
        ...


class ProviderRegistry:
    """Registry for provider adapter instances.

    Backed by a dict keyed by provider name. Registration is idempotent.
    """

    def __init__(self) -> None:
        self._providers: dict[str, ProviderAdapter] = {}

    def register(self, provider: ProviderAdapter) -> None:
        """Register a provider. Overwrites if name already exists."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> ProviderAdapter | None:
        """Get a provider by name, or None if not found."""
        return self._providers.get(name)

    def get_all(self) -> list[ProviderAdapter]:
        """Return all registered providers."""
        return list(self._providers.values())

    def list_names(self) -> list[str]:
        """Return all registered provider names."""
        return list(self._providers.keys())
