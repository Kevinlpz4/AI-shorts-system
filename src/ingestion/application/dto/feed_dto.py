"""
Feed DTOs — representaciones de datos de Feed.

DTOs:
    - FeedSummaryDTO: Vista resumida (sin relaciones ni sync_policy).
    - FeedDetailDTO: Vista completa con sync_policy y relaciones.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeedSummaryDTO:
    """Resumen de un Feed.

    Attributes:
        id: ID único del feed.
        source_id: ID del NewsSource padre.
        url: URL del feed.
        label: Título o etiqueta legible.
        language: Código ISO 639-1 del idioma.
        is_active: Si está habilitado para fetch.
        retry_count: Contador de fallos consecutivos.
    """

    id: str
    source_id: str
    url: str
    label: str
    language: str
    is_active: bool
    retry_count: int = 0


@dataclass(frozen=True)
class FeedDetailDTO:
    """Detalle completo de un Feed.

    Attributes:
        id: ID único del feed.
        source_id: ID del NewsSource padre.
        url: URL del feed.
        label: Título o etiqueta legible.
        language: Código ISO 639-1 del idioma.
        is_active: Si está habilitado para fetch.
        sync_mode: Modo de sincronización (PULL, PUSH, STREAM, MANUAL).
        sync_interval_minutes: Intervalo en minutos.
        sync_max_retries: Máximo de reintentos.
        categories: IDs de categorías asignadas.
        topics: IDs de topics asignados.
        retry_count: Contador de fallos consecutivos.
    """

    id: str
    source_id: str
    url: str
    label: str
    language: str
    is_active: bool
    sync_mode: str = "PULL"
    sync_interval_minutes: int | None = None
    sync_max_retries: int = 3
    categories: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    retry_count: int = 0
