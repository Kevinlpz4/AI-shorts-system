"""
SourceRegistry — manages SourceDefinition instances.

Sources are registered by id and can be queried by technology,
enabled status, or retrieved in bulk.

Usage::

    from runtime.registry.source_registry import SourceRegistry

    registry = SourceRegistry()
    registry.register(source)
    enabled = registry.get_enabled()
"""
from __future__ import annotations

from runtime.contracts.source_definition import SourceDefinition


class SourceRegistry:
    """Registry for SourceDefinition instances.

    Backed by a dict keyed by source id. Registration is idempotent
    (same id overwrites).
    """

    def __init__(self) -> None:
        self._sources: dict[str, SourceDefinition] = {}

    def register(self, source: SourceDefinition) -> None:
        """Register a source definition. Overwrites if id already exists."""
        self._sources[source.id] = source

    def get(self, source_id: str) -> SourceDefinition | None:
        """Get a source by id, or None if not found."""
        return self._sources.get(source_id)

    def get_all(self) -> list[SourceDefinition]:
        """Return all registered sources."""
        return list(self._sources.values())

    def get_enabled(self) -> list[SourceDefinition]:
        """Return only enabled sources."""
        return [s for s in self._sources.values() if s.enabled]

    def list_by_technology(self, technology: str) -> list[SourceDefinition]:
        """Return sources matching a technology (e.g., ``'rss'``, ``'api'``)."""
        return [s for s in self._sources.values() if s.technology == technology]
