"""
ResearchTopic — Aggregate Root del módulo Research
====================================================
Entidad principal. Es la RAÍZ del agregado: todo acceso a datos
de investigación pasa por acá.

Tiene identidad (UUID), ciclo de vida (FOUND → PENDING_REVIEW → APPROVED/REJECTED),
y emite eventos de dominio cuando su estado cambia.

Reglas de negocio que ENFORZA:
  1. Solo se puede aprobar/rechazar un topic en PENDING_REVIEW
  2. Una vez APPROVED o REJECTED, no se puede cambiar
  3. Al crear, va automáticamente a PENDING_REVIEW (control editorial)
  4. Los eventos se acumulan y se extraen con pull_events()

Responsabilidad ÚNICA (SRP):
  Representar un topic de investigación y controlar su ciclo de vida.
  NO sabe de fuentes externas, persistencia, ni presentación.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from research.domain.value_objects.research_score import ResearchScore
from research.domain.value_objects.research_source import ResearchSource
from research.domain.value_objects.research_status import ResearchStatus
from research.domain.exceptions import ResearchAlreadyReviewedError
from research.domain.events import (
    DomainEvent,
    TopicDiscovered,
    TopicApproved,
    TopicRejected,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ResearchTopic:
    """
    Aggregate Root del módulo Research.

    Attributes:
        id: Identidad única del topic
        title: Título de la noticia/tema
        description: Resumen breve (1-2 líneas)
        content: Contenido completo
        source: Origen de la información
        score: Puntaje calculado
        status: Estado actual del ciclo de vida
        url: URL original (si aplica)
        author: Autor (si aplica)
        published_at: Fecha de publicación original
        created_at: Fecha de descubrimiento
        reviewed_at: Fecha de revisión humana
        duplicate_hash: Hash para detección de duplicados
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    content: str = ""
    source: ResearchSource = field(default_factory=lambda: ResearchSource.manual())
    score: ResearchScore = field(default_factory=ResearchScore)
    status: ResearchStatus = ResearchStatus.default()
    url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=_utcnow)
    reviewed_at: Optional[datetime] = None
    duplicate_hash: Optional[str] = None

    # Eventos de dominio acumulados (se limpian con pull_events)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    # ──────────────────────────────────────────────
    # Comportamiento de dominio
    # ──────────────────────────────────────────────

    def approve(self) -> None:
        """
        Aprueba el topic para generación de contenido.

        Solo se puede aprobar si está en PENDING_REVIEW.
        Dispara el evento TopicApproved.

        Raises:
            ResearchAlreadyReviewedError: si ya fue aprobado/rechazado
        """
        if self.status.is_terminal:
            raise ResearchAlreadyReviewedError(
                status=self.status.value,
                detail=f"Topic ya fue {self.status.value}"
            )
        if not self.status.is_reviewable:
            self._move_to_pending_review()

        self.status = ResearchStatus.APPROVED
        self.reviewed_at = _utcnow()
        self._events.append(
            TopicApproved(
                topic_id=self.id,
                title=self.title,
                approved_at=self.reviewed_at,
            )
        )

    def reject(self, reason: str = "") -> None:
        """
        Rechaza el topic (no se generará contenido).

        Solo se puede rechazar si está en PENDING_REVIEW.
        Dispara el evento TopicRejected.

        Args:
            reason: Motivo del rechazo (opcional, para analytics)

        Raises:
            ResearchAlreadyReviewedError: si ya fue aprobado/rechazado
        """
        if self.status.is_terminal:
            raise ResearchAlreadyReviewedError(
                status=self.status.value,
                detail=f"Topic ya fue {self.status.value}"
            )
        if not self.status.is_reviewable:
            self._move_to_pending_review()

        self.status = ResearchStatus.REJECTED
        self.reviewed_at = _utcnow()
        self._events.append(
            TopicRejected(
                topic_id=self.id,
                title=self.title,
                reason=reason,
                rejected_at=self.reviewed_at,
            )
        )

    def mark_as_discovered(self) -> None:
        """
        Marca el topic como descubierto y emite el evento.

        Se llama después de que el caso de uso procesa el topic
        (dedup + scoring) y lo deja listo para aprobación humana.
        """
        self._events.append(
            TopicDiscovered(
                topic_id=self.id,
                title=self.title,
                source_name=self.source.name,
                score_total=self.score.total,
            )
        )

    # ──────────────────────────────────────────────
    # Eventos
    # ──────────────────────────────────────────────

    def pull_events(self) -> list[DomainEvent]:
        """
        Extrae y limpia los eventos acumulados.

        El caso de uso llama a este método después de ejecutar
        la operación y publica los eventos en el EventBus.

        Returns:
            Lista de eventos pendientes de publicar
        """
        events = self._events
        self._events = []
        return events

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _move_to_pending_review(self) -> None:
        """Transiciona de FOUND a PENDING_REVIEW automáticamente."""
        if self.status == ResearchStatus.FOUND:
            self.status = ResearchStatus.PENDING_REVIEW

    def __str__(self) -> str:
        return (
            f"ResearchTopic('{self.title[:50]}...' | "
            f"{self.status.value} | "
            f"score={self.score.total:.1f})"
        )
