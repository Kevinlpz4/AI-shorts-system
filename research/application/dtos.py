"""
Application DTOs — Data Transfer Objects for Research module
==============================================================
Los DTOs son objetos planos que transportan datos entre capas.
No tienen lógica de negocio, no heredan de entidades.

Propósito:
  - Aislar la capa de presentación (CLI, API) del dominio
  - Definir contratos claros de entrada/salida
  - Solo contienen datos, sin comportamiento
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


# ── Input DTOs ────────────────────────────────────────


@dataclass
class ManualInputDTO:
    """
    DTO de entrada: lo que provee el usuario al agregar un topic manualmente.

    Todos los campos son opcionales porque el usuario puede proveer
    solo un enlace, solo un texto, o ambos.

    Atributos:
        url: Enlace a la noticia
        title: Título (si no se provee, se extrae de la URL)
        content: Contenido o texto libre
        description: Descripción corta
        author: Autor de la noticia
        source_name: Nombre custom de la fuente (default "manual")
    """
    url: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    source_name: str = "manual"


@dataclass
class AutoDiscoverDTO:
    """
    DTO de entrada: parámetros para el descubrimiento automático.

    Atributos:
        query: Término de búsqueda (None = trending)
        limit: Resultados por fuente
        source_names: Fuentes específicas (None = todas las disponibles)
    """
    query: Optional[str] = None
    limit: int = 10
    source_names: Optional[list[str]] = None


@dataclass
class ReviewDecisionDTO:
    """
    DTO de entrada: decisión del usuario sobre un topic.

    Atributos:
        topic_id: ID del topic a aprobar/rechazar
        reject_reason: Motivo de rechazo (opcional)
    """
    topic_id: UUID
    reject_reason: str = ""


@dataclass
class ListTopicsQuery:
    """
    DTO de entrada: filtros para listar topics.

    Atributos:
        status: Filtrar por estado (None = todos)
        limit: Máximo de resultados
        offset: Paginación
    """
    status: Optional[str] = None  # pending_review, approved, rejected, found
    limit: int = 20
    offset: int = 0


# ── Output DTOs ───────────────────────────────────────


@dataclass
class ResearchTopicDTO:
    """
    DTO de salida: representación pública de un ResearchTopic.

    No expone _events ni datos internos del agregado.

    Atributos:
        id: UUID del topic
        title: Título
        description: Resumen
        content_preview: Primeros 200 chars del contenido
        source_name: Nombre de la fuente
        source_type: Tipo de fuente (manual/automatic)
        status: Estado actual
        score_total: Puntaje total
        score_components: Componentes del score
        url: URL original
        author: Autor
        created_at: Fecha de descubrimiento
        reviewed_at: Fecha de revisión
    """
    id: UUID
    title: str
    description: str
    content_preview: str
    source_name: str
    source_type: str
    status: str
    score_total: float
    score_components: dict
    url: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None


@dataclass
class ResearchResultDTO:
    """
    DTO de salida: resultado de una operación de descubrimiento.

    Atributos:
        topic: El topic creado/afectado
        is_duplicate: Si se detectó como duplicado
        events: Eventos de dominio generados
    """
    topic: ResearchTopicDTO
    is_duplicate: bool = False
    events: list[dict] = field(default_factory=list)


@dataclass
class DiscoverBatchResultDTO:
    """
    DTO de salida: resultado de descubrimiento batch (múltiples fuentes).

    Atributos:
        discovered: Topics nuevos no duplicados
        duplicates: Topics que ya existían
        errors: Fuentes que fallaron
    """
    discovered: list[ResearchTopicDTO]
    duplicates: list[ResearchTopicDTO]
    errors: list[dict]


@dataclass
class ReviewResultDTO:
    """
    DTO de salida: resultado de aprobar/rechazar un topic.

    Atributos:
        topic: El topic actualizado
        events: Eventos de dominio generados
    """
    topic: ResearchTopicDTO
    events: list[dict]
