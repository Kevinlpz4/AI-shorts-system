"""
Feed — Aggregate Root del BC Ingestion.

Representa un stream específico y configurable de información dentro de un
NewsSource. Es la unidad ejecutable de ingesta con reglas de reintentos,
pausa automática y categorización.

Ciclo de vida: Creado → Activo → Pausado (por errores) → Inactivo (manual)

Invariantes:
  - I-05: url MUST NOT be empty (validated by ArticleUrl VO)
  - I-06: url MUST be unique within the parent NewsSource (enforced by repository)
  - I-07: retry_count MUST be 0 after successful collection
  - I-08: MUST pause if retry_count >= max_retries and fetch fails
  - I-09: MUST NOT fetch while paused (application layer)
  - I-10: MUST NOT fetch if is_active = False (application layer)

Eventos emitidos:
  - RawArticleCollected: cuando record_collection() es llamado con count > 0

Cross-AR rules (Application Layer):
  - AL-03: source_id debe referenciar un NewsSource existente
  - AL-04: No crear Feed bajo un NewsSource inactivo
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from foundation.base.aggregate_root import AggregateRoot

from ingestion.domain.entities._categorizable import _Categorizable
from ingestion.domain.entities.ids import CategoryId, FeedId, SourceId, TopicId
from ingestion.domain.events.ingestion_events import RawArticleCollected
from ingestion.domain.value_objects.article_title import ArticleTitle
from ingestion.domain.value_objects.article_url import ArticleUrl
from ingestion.domain.value_objects.language import Language
from ingestion.domain.value_objects.sync_mode import SyncMode
from ingestion.domain.value_objects.sync_policy import SyncPolicy


@dataclass(eq=False, init=False)
class Feed(AggregateRoot, _Categorizable):
    """Stream configurable de información dentro de un NewsSource.

    Attributes:
        id: Identidad única del feed.
        source_id: Referencia al NewsSource padre (por ID).
        url: URL del feed (endpoint de consulta).
        label: Título o etiqueta legible.
        language: Idioma del contenido del feed.
        is_active: Si está habilitado para fetch.
        sync_policy: Política de sincronización.
        categories: Categorías asignadas directamente al feed.
        topics: Topics de interés asociados.
        retry_count: Contador de fallos consecutivos actuales.
    """

    id: FeedId
    source_id: SourceId
    url: ArticleUrl
    label: ArticleTitle
    language: Language
    is_active: bool = True
    sync_policy: SyncPolicy = field(
        default_factory=lambda: SyncPolicy(
            mode=SyncMode.PULL, interval_minutes=30  # type: ignore[arg-type]
        )
    )
    categories: list[CategoryId] = field(default_factory=list)
    topics: list[TopicId] = field(default_factory=list)
    retry_count: int = 0

    def __init__(
        self,
        id: FeedId,
        source_id: SourceId,
        url: ArticleUrl,
        label: ArticleTitle,
        language: Language,
        is_active: bool = True,
        sync_policy: SyncPolicy | None = None,
        categories: list[CategoryId] | None = None,
        topics: list[TopicId] | None = None,
        retry_count: int = 0,
    ) -> None:
        """Initialize a Feed.

        Args:
            id: Identidad única del feed.
            source_id: Referencia al NewsSource padre.
            url: URL del feed.
            label: Título o etiqueta legible.
            language: Idioma del contenido.
            is_active: Si está habilitado para fetch (default: True).
            sync_policy: Política de sincronización (default: PULL/30min).
            categories: Categorías asignadas (default: []).
            topics: Topics de interés (default: []).
            retry_count: Contador de reintentos (default: 0).
        """
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "url", url)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "is_active", is_active)
        object.__setattr__(
            self,
            "sync_policy",
            sync_policy or SyncPolicy(mode=SyncMode.PULL, interval_minutes=30),  # type: ignore[arg-type]
        )
        object.__setattr__(self, "categories", categories or [])
        object.__setattr__(self, "topics", topics or [])
        object.__setattr__(self, "retry_count", retry_count)
        object.__setattr__(self, "_events", [])

    def record_collection(self, batch_id: UUID | None = None, count: int = 0) -> None:
        """Registra un fetch exitoso.

        Resetea retry_count a 0. Emite RawArticleCollected si count > 0.

        Args:
            batch_id: UUID del batch (se auto-genera si no se provee).
            count: Cantidad de artículos nuevos obtenidos.
        """
        self.retry_count = 0
        if count > 0:
            actual_batch_id = batch_id or uuid4()
            self.register_event(
                RawArticleCollected(
                    feed_id=self.id,
                    batch_id=actual_batch_id,
                    count=count,
                    collected_at=datetime.now(timezone.utc),
                )
            )

    def record_failure(self, error: str) -> FeedFailureResult:
        """Registra un fallo de fetch.

        Incrementa retry_count. Si not can_retry(), marca auto-pause.

        Args:
            error: Descripción del error.

        Returns:
            FeedFailureResult indicando si se pausó y el contador actual.
        """
        self.retry_count += 1
        if not self.can_retry():
            self.is_active = False
            return FeedFailureResult(paused=True, retry_count=self.retry_count)
        return FeedFailureResult(paused=False, retry_count=self.retry_count)

    def can_retry(self) -> bool:
        """Verifica si el feed puede reintentar.

        Returns:
            True si retry_count < sync_policy.max_retries.
        """
        return self.retry_count < self.sync_policy.max_retries

    def pause(self, reason: str) -> None:
        """Pausa el feed manualmente.

        Marca is_active = False. Requiere reactivación manual.

        Args:
            reason: Razón de la pausa.
        """
        self.is_active = False

    def activate(self) -> None:
        """Reactivar el feed.

        Marca is_active = True, resetea retry_count a 0.
        """
        self.is_active = True
        self.retry_count = 0

    def assign_category(self, category_id: CategoryId) -> None:
        """Agrega una categoría al feed.

        No valida existencia (consistencia eventual).
        """
        self._assign_category(self.categories, category_id)

    def remove_category(self, category_id: CategoryId) -> None:
        """Remueve una categoría del feed."""
        self._remove_category(self.categories, category_id)

    def assign_topic(self, topic_id: TopicId) -> None:
        """Agrega un topic al feed.

        No valida existencia (consistencia eventual).
        """
        self._assign_topic(self.topics, topic_id)

    def remove_topic(self, topic_id: TopicId) -> None:
        """Remueve un topic del feed."""
        self._remove_topic(self.topics, topic_id)

    def update_sync_policy(self, policy: SyncPolicy) -> None:
        """Actualiza la política de sincronización.

        Args:
            policy: Nueva política de sincronización.
        """
        self.sync_policy = policy


@dataclass(frozen=True)
class FeedFailureResult:
    """Resultado de Feed.record_failure().

    Attributes:
        paused: True si el feed se auto-pausó por exceder max_retries.
        retry_count: Valor del contador de reintentos después del fallo.
    """

    paused: bool
    retry_count: int
