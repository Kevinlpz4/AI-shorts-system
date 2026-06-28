"""
Tests de integración para GoogleNewsRSSSource.

Requiere conexión a internet.
Se ejecutan solo con: pytest -m integration
"""
import pytest

from research.infrastructure.sources.google_news_rss import GoogleNewsRSSSource


@pytest.mark.integration
class TestGoogleNewsRSSSourceIntegration:
    """Tests que llaman al RSS real de Google News."""

    @pytest.mark.asyncio
    async def test_fetch_top_stories(self):
        """Obtener top stories sin query debe funcionar."""
        source = GoogleNewsRSSSource(locale="es-419")
        try:
            results = await source.fetch(limit=5)
            assert len(results) >= 1
            assert results[0].title
            assert results[0].url
        finally:
            await source.close()

    @pytest.mark.asyncio
    async def test_fetch_with_query(self):
        """Buscar por query debe retornar resultados relevantes."""
        source = GoogleNewsRSSSource(locale="es-419")
        try:
            results = await source.fetch(query="inteligencia artificial", limit=5)
            assert len(results) >= 1
            # El título debe mencionar IA o inteligencia
            titles = " ".join(r.title.lower() for r in results)
            assert any(word in titles for word in ["ia", "inteligencia", "artificial"])
        finally:
            await source.close()

    @pytest.mark.asyncio
    async def test_fetch_english_top_stories(self):
        """Top stories en inglés debe funcionar."""
        source = GoogleNewsRSSSource(locale="en-US", country="US")
        try:
            results = await source.fetch(limit=3)
            assert len(results) >= 1
        finally:
            await source.close()

    @pytest.mark.asyncio
    async def test_fetch_respects_limit(self):
        """El límite de resultados debe respetarse."""
        source = GoogleNewsRSSSource(locale="es-419")
        try:
            results = await source.fetch(query="tecnología", limit=3)
            assert len(results) <= 3
        finally:
            await source.close()

    @pytest.mark.asyncio
    async def test_fetch_returns_raw_data(self):
        """Los resultados deben ser RawResearchData con campos completos."""
        from research.domain.ports.research_source import RawResearchData

        source = GoogleNewsRSSSource(locale="es-419")
        try:
            results = await source.fetch(query="ciencia", limit=2)
            assert len(results) >= 1
            item = results[0]
            assert isinstance(item, RawResearchData)
            assert item.title
            assert item.url
            assert item.published_at is not None
        finally:
            await source.close()

    @pytest.mark.asyncio
    async def test_source_name(self):
        """source_name debe ser 'google-news-rss'."""
        source = GoogleNewsRSSSource()
        assert source.source_name == "google-news-rss"
        await source.close()

    @pytest.mark.asyncio
    async def test_available(self):
        """Siempre debe estar disponible."""
        source = GoogleNewsRSSSource()
        assert source.available is True
        await source.close()
