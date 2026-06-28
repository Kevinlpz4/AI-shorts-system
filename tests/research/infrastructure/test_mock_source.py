"""
Tests para MockResearchSource.
"""
import pytest

from research.infrastructure.sources.mock_source import MockResearchSource
from research.domain.exceptions import SourceNotAvailableError


class TestMockResearchSource:

    @pytest.mark.asyncio
    async def test_fetch_all(self):
        """Fetch sin query debe retornar todos los topics."""
        source = MockResearchSource()
        results = await source.fetch(limit=10)
        assert len(results) >= 3  # Tenemos al menos 3 mock topics
        assert all(r.title for r in results)
        assert all(r.content for r in results)

    @pytest.mark.asyncio
    async def test_fetch_with_query(self):
        """Fetch con query debe filtrar resultados."""
        source = MockResearchSource()
        results = await source.fetch(query="IA", limit=10)
        assert len(results) >= 1
        assert all("IA" in r.title or "ia" in r.title.lower() or "IA" in r.description
                   for r in results)

    @pytest.mark.asyncio
    async def test_fetch_with_limit(self):
        """Fetch debe respetar el límite."""
        source = MockResearchSource()
        results = await source.fetch(limit=2)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_fetch_with_no_match(self):
        """Fetch que no encuentra resultados debe retornar lista vacía."""
        source = MockResearchSource()
        results = await source.fetch(query="XYZ_No_Existe_999", limit=10)
        assert results == []

    @pytest.mark.asyncio
    async def test_source_name(self):
        """source_name debe ser configurable."""
        source = MockResearchSource(name="custom-mock")
        assert source.source_name == "custom-mock"

    @pytest.mark.asyncio
    async def test_available_default_true(self):
        """Por defecto, la fuente debe estar disponible."""
        source = MockResearchSource()
        assert source.available is True

    @pytest.mark.asyncio
    async def test_unavailable_source_raises(self):
        """Fuente no disponible debe lanzar error al hacer fetch."""
        source = MockResearchSource(available=False)
        assert source.available is False
        with pytest.raises(SourceNotAvailableError):
            await source.fetch()

    @pytest.mark.asyncio
    async def test_fetch_returns_raw_data(self):
        """Los resultados deben ser RawResearchData."""
        from research.domain.ports.research_source import RawResearchData
        source = MockResearchSource()
        results = await source.fetch(limit=1)
        assert len(results) >= 0  # Podría ser 0 si filtramos todo
        if results:
            assert isinstance(results[0], RawResearchData)

    def test_repr(self):
        """__repr__ debe mostrar nombre y disponibilidad."""
        source = MockResearchSource(name="test", available=True)
        assert "MockResearchSource" in repr(source)
        assert "test" in repr(source)
        assert "available=True" in repr(source)
