"""
Feed Commands — operaciones CRUD, estado y fetch para Feed.

Commands:
    - RegisterFeedCommand: Crear nuevo feed bajo un NewsSource.
    - UpdateFeedCommand: Actualizar configuración de feed existente.
    - PauseFeedCommand: Pausar feed manualmente.
    - ActivateFeedCommand: Reactivar feed.
    - RecordCollectionCommand: Registrar fetch exitoso.
    - RecordFailureCommand: Registrar fallo de fetch.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterFeedCommand:
    """Crear un nuevo feed bajo un NewsSource.

    Attributes:
        source_id: ID del NewsSource padre.
        url: URL del feed (endpoint de consulta).
        label: Título o etiqueta legible.
        language: Código ISO 639-1 del idioma.
        sync_mode: Modo de sincronización (PULL|PUSH|STREAM|MANUAL).
        sync_interval_minutes: Intervalo en minutos (requerido para PULL).
        sync_max_retries: Máximo de reintentos antes de pausar (default: 3).
        categories: IDs de categorías asignadas (default: empty).
        topics: IDs de topics asignados (default: empty).
    """

    source_id: str
    url: str
    label: str
    language: str
    sync_mode: str = "PULL"
    sync_interval_minutes: int | None = 30
    sync_max_retries: int = 3
    categories: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()


@dataclass(frozen=True)
class UpdateFeedCommand:
    """Actualizar configuración de un feed existente.

    Todos los campos excepto ``feed_id`` son opcionales.
    Solo se actualizan los campos provistos (no None).

    Attributes:
        feed_id: ID del feed a actualizar.
        url: Nueva URL (opcional).
        label: Nueva etiqueta (opcional).
        language: Nuevo código de idioma (opcional).
        sync_mode: Nuevo modo de sincronización (opcional).
        sync_interval_minutes: Nuevo intervalo (opcional).
        sync_max_retries: Nuevo máximo de reintentos (opcional).
    """

    feed_id: str
    url: str | None = None
    label: str | None = None
    language: str | None = None
    sync_mode: str | None = None
    sync_interval_minutes: int | None = None
    sync_max_retries: int | None = None


@dataclass(frozen=True)
class PauseFeedCommand:
    """Pausar un feed manualmente.

    Marca el feed como inactivo. Requiere reactivación manual.

    Attributes:
        feed_id: ID del feed a pausar.
        reason: Razón de la pausa.
    """

    feed_id: str
    reason: str


@dataclass(frozen=True)
class ActivateFeedCommand:
    """Reactivar un feed previamente pausado.

    Resetea ``retry_count`` a 0 y marca como activo.

    Attributes:
        feed_id: ID del feed a reactivar.
    """

    feed_id: str


@dataclass(frozen=True)
class RecordCollectionCommand:
    """Registrar un fetch exitoso de un feed.

    Resetea ``retry_count`` a 0. Emite evento si ``count > 0``.

    Attributes:
        feed_id: ID del feed que completó el fetch.
        count: Cantidad de artículos nuevos obtenidos.
        batch_id: UUID del batch (opcional, se auto-genera si no se provee).
    """

    feed_id: str
    count: int
    batch_id: str | None = None


@dataclass(frozen=True)
class RecordFailureCommand:
    """Registrar un fallo de fetch de un feed.

    Incrementa ``retry_count``. Si excede ``max_retries``, el feed
    se auto-pausa.

    Attributes:
        feed_id: ID del feed que falló.
        error: Descripción del error.
    """

    feed_id: str
    error: str
