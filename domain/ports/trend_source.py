from typing import Protocol, Optional

from domain.entities.trend import Trend


class TrendSourcePort(Protocol):
    """
    Puerto: Fuente de tendencias.
    
    Implementaciones: News API, Twitter, YouTube, Reddit, Mock.
    """
    
    async def fetch_trends(
        self,
        niche: Optional[str] = None,
        limit: int = 20,
    ) -> list[Trend]:
        """Obtiene tendencias de esta fuente."""
        ...

    @property
    def source_name(self) -> str:
        """Nombre de la fuente (news, twitter, etc.)"""
        ...

    @property
    def available(self) -> bool:
        ...
