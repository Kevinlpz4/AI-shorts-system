"""
Tests para SourceRegistry.
"""
import pytest

from research.application.source_registry import SourceRegistry
from research.domain.ports.research_source import ResearchSourcePort
from research.domain.exceptions import SourceNotAvailableError


class MockSource:
    """Source mock mínimo para tests del registry."""

    def __init__(self, name: str, available: bool = True):
        self._name = name
        self._available = available

    @property
    def source_name(self) -> str:
        return self._name

    @property
    def available(self) -> bool:
        return self._available

    async def fetch(self, query=None, limit=10):
        if not self._available:
            raise SourceNotAvailableError(source_name=self._name)
        return []


class TestSourceRegistry:

    def test_register_and_get(self):
        registry = SourceRegistry()
        source = MockSource("test-source")
        registry.register(source)

        retrieved = registry.get("test-source")
        assert retrieved.source_name == "test-source"

    def test_get_unregistered_raises(self):
        registry = SourceRegistry()
        with pytest.raises(SourceNotAvailableError):
            registry.get("no-existe")

    def test_register_duplicate_raises(self):
        registry = SourceRegistry()
        registry.register(MockSource("test"))
        with pytest.raises(ValueError, match="(?i)ya existe"):
            registry.register(MockSource("test"))

    def test_get_all_available(self):
        registry = SourceRegistry()
        registry.register(MockSource("source-1", available=True))
        registry.register(MockSource("source-2", available=False))
        registry.register(MockSource("source-3", available=True))

        available = registry.get_all_available()
        assert len(available) == 2
        names = [s.source_name for s in available]
        assert "source-1" in names
        assert "source-3" in names
        assert "source-2" not in names

    def test_list_sources(self):
        registry = SourceRegistry()
        registry.register(MockSource("src-a", available=True))
        registry.register(MockSource("src-b", available=False))

        sources = registry.list_sources()
        assert len(sources) == 2
        assert {"name": "src-a", "available": True} in sources
        assert {"name": "src-b", "available": False} in sources

    def test_contains(self):
        registry = SourceRegistry()
        registry.register(MockSource("exists"))
        assert "exists" in registry
        assert "no-existe" not in registry

    @pytest.mark.asyncio
    async def test_get_unavailable_source_raises_on_fetch(self):
        """Fuente no disponible debe fallar al hacer fetch."""
        registry = SourceRegistry()
        source = MockSource("down", available=False)
        registry.register(source)

        retrieved = registry.get("down")
        assert retrieved.available is False

        with pytest.raises(SourceNotAvailableError):
            await retrieved.fetch()
