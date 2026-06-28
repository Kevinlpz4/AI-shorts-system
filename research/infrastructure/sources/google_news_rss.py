"""
GoogleNewsRSSSource — Fuente de investigación via RSS de Google News
======================================================================
Adapter real que obtiene noticias desde Google News usando su RSS feed.

NO requiere API key.
100 requests por query son gratis y sin límite de rate (RSS público).

Formato de URL:
  Search:  https://news.google.com/rss/search?q={query}&hl={locale}
  Top:     https://news.google.com/rss?hl={locale}&gl={country}

Locale examples: es-419 (LatAm), es (España), en-US, pt-BR, etc.

Uso:
    source = GoogleNewsRSSSource(locale="es-419")
    results = await source.fetch(query="inteligencia artificial", limit=5)

Integración hexagonal:
  - Implementa ResearchSourcePort (Protocol)
  - Se registra en SourceRegistry desde el Composition Root
  - El dominio no conoce esta clase
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

import aiohttp
import feedparser

from research.domain.ports.research_source import ResearchSourcePort, RawResearchData


# ── Configuración ───────────────────────────────────

_BASE_URL = "https://news.google.com/rss"
_DEFAULT_LOCALE = "es-419"  # Español Latinoamérica
_DEFAULT_COUNTRY = "US"
_REQUEST_TIMEOUT = 15  # segundos
_MAX_RESULTS = 100  # máximo que devuelve Google News RSS


class GoogleNewsRSSSource:
    """
    Fuente de noticias via RSS de Google News.

    Atributos:
        source_name: identificador único ('google-news-rss')
        available: True si el servicio está operativo
        locale: código de idioma/región (ej: es-419, en-US)
    """

    def __init__(
        self,
        locale: str = _DEFAULT_LOCALE,
        country: str = _DEFAULT_COUNTRY,
    ):
        self._locale = locale
        self._country = country
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def source_name(self) -> str:
        return "google-news-rss"

    @property
    def available(self) -> bool:
        """Siempre disponible (RSS público sin auth)."""
        return True

    async def fetch(
        self,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> list[RawResearchData]:
        """
        Obtiene noticias desde Google News RSS.

        Args:
            query: Término de búsqueda (None = top stories)
            limit: Máximo de resultados (default 10, max 100)

        Returns:
            Lista de RawResearchData con datos normalizados

        Raises:
            SourceNotAvailableError: si hay error de red/timeout
        """
        url = self._build_url(query)
        raw_xml = await self._fetch_rss(url)

        feed = feedparser.parse(raw_xml)
        if feed.bozo and not feed.entries:
            # bozo = error de parseo, pero si hay entries igual sirve
            from research.domain.exceptions import SourceNotAvailableError
            raise SourceNotAvailableError(
                source_name=self.source_name,
                detail=f"Error al parsear RSS: {feed.bozo_exception}",
            )

        results: list[RawResearchData] = []
        for entry in feed.entries[:limit]:
            raw = self._entry_to_raw(entry)
            if raw and raw.title:
                results.append(raw)

        return results

    # ── URL Construction ────────────────────────────

    def _build_url(self, query: Optional[str]) -> str:
        """
        Construye la URL del RSS según si hay query o no.

        Search: /rss/search?q=...
        Top stories: /rss?hl=...&gl=...&ceid=...
        """
        if query:
            return (
                f"{_BASE_URL}/search"
                f"?q={self._url_encode(query)}"
                f"&hl={self._locale}"
                f"&gl={self._country}"
            )
        return (
            f"{_BASE_URL}"
            f"?hl={self._locale}"
            f"&gl={self._country}"
            f"&ceid={self._country}:{self._locale.split('-')[0]}"
        )

    @staticmethod
    def _url_encode(query: str) -> str:
        """Codifica query para URL (reemplaza espacios con +)."""
        from urllib.parse import quote
        return quote(query, safe='+')

    # ── HTTP ────────────────────────────────────────

    async def _fetch_rss(self, url: str) -> str:
        """
        Fetch del XML RSS usando aiohttp.

        Maneja:
          - Timeout
          - Errores HTTP
          - Redirects (automático con aiohttp)
        """
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT),
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                    },
                )

            async with self._session.get(url) as response:
                if response.status != 200:
                    from research.domain.exceptions import SourceNotAvailableError
                    raise SourceNotAvailableError(
                        source_name=self.source_name,
                        detail=f"HTTP {response.status} al consultar Google News RSS",
                    )
                return await response.text()

        except SourceNotAvailableError:
            raise
        except asyncio.TimeoutError:
            from research.domain.exceptions import SourceNotAvailableError
            raise SourceNotAvailableError(
                source_name=self.source_name,
                detail="Timeout al consultar Google News RSS",
            )
        except Exception as e:
            from research.domain.exceptions import SourceNotAvailableError
            raise SourceNotAvailableError(
                source_name=self.source_name,
                detail=f"Error de conexión: {e}",
            )

    # ── Mapping ─────────────────────────────────────

    def _entry_to_raw(self, entry) -> Optional[RawResearchData]:
        """
        Convierte una entrada de feedparser → RawResearchData.

        Maneja:
          - Título (puede venir con prefijo del source type)
          - Link (Google redirect URL)
          - Descripción (puede ser HTML o texto plano)
          - Fecha de publicación
          - Source name (extraído del tag <source> si existe)
        """
        try:
            title = entry.get("title", "").strip()
            if not title:
                return None

            # El link de Google News es un redirect, pero sirve como URL única
            link = entry.get("link", "").strip()

            # Descripción: limpiar HTML básico si viene
            description = entry.get("summary", entry.get("description", ""))
            description = self._clean_html(description)[:500]

            # Fecha de publicación
            published = None
            pub_tuple = entry.get("published_parsed")
            if pub_tuple:
                try:
                    from time import mktime
                    published = datetime.fromtimestamp(
                        mktime(pub_tuple), tz=timezone.utc
                    )
                except Exception:
                    published = None

            # Source name: puede venir en <source> tag
            source_name = None
            if hasattr(entry, "source") and entry.source:
                source_detail = entry.source
                if hasattr(source_detail, "title"):
                    source_name = source_detail.title

            return RawResearchData(
                title=title,
                description=description,
                content="",  # RSS no trae contenido completo
                url=link,
                author=source_name,  # Usamos source como "autor"
                published_at=published,
            )

        except Exception:
            return None

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remueve tags HTML básicos de un texto."""
        import re
        # Remover tags HTML
        text = re.sub(r'<[^>]+>', ' ', text)
        # Colapsar espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        # Decodificar entidades HTML básicas
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        return text.strip()

    # ── Lifecycle ───────────────────────────────────

    async def close(self) -> None:
        """Cierra la sesión HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()

    def __repr__(self) -> str:
        return (
            f"GoogleNewsRSSSource(locale='{self._locale}', "
            f"country='{self._country}')"
        )
