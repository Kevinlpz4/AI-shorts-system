"""
Research Domain Events
======================
Eventos de dominio que el módulo Research emite.

Cada evento representa algo que SUCEDIÓ en el dominio.
Son inmutables, llevan el timestamp de cuando ocurrieron.

Ningún evento contiene lógica — solo datos.

Consumer examples (futuro):
  - TopicDiscovered → Script Generator puede empezar a generar ideas
  - TopicApproved → Scheduler puede encolar la generación
  - TopicRejected → Analytics registra el rechazo para mejorar el scoring

Formato standard:
  - topic_id: UUID del ResearchTopic afectado
  - occurred_at: datetime UTC de cuando ocurrió

NOTA sobre herencia de dataclasses:
  Python NO soporta bien herencia de dataclasses con defaults mezclados.
  Por eso cada evento es standalone en lugar de heredar de DomainEvent.
  DomainEvent es solo una clase base para type checking, no un dataclass.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID


def _utcnow() -> datetime:
    """Helper para timestamp consistente."""
    return datetime.now(timezone.utc)


class DomainEvent:
    """
    Base type para todos los eventos de dominio.

    No es un dataclass — solo para type checking.
    Cada subclase es un dataclass independiente.
    """
    occurred_at: datetime
    topic_id: UUID

    def __post_init__(self):
        """Hook opcional para validación post-creación."""
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convierte el evento a dict para serialización."""
        return {
            "type": self.__class__.__name__,
            "data": {
                k: str(v) if isinstance(v, UUID) else v.isoformat() if isinstance(v, datetime) else v
                for k, v in self.__dict__.items()
                if not k.startswith("_")
            },
        }


@dataclass(frozen=True)
class TopicDiscovered(DomainEvent):
    """
    Se descubrió un nuevo topic de investigación.

    Se emite cuando:
      - Una fuente automática encuentra una noticia
      - El usuario ingresa contenido manualmente

    Futuros consumers:
      - Script Generator: puede pre-generar ideas automáticamente
      - Analytics: registra el descubrimiento
    """
    topic_id: UUID
    title: str
    source_name: str
    score_total: float
    occurred_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True)
class TopicApproved(DomainEvent):
    """
    Un topic fue aprobado por el usuario.

    Este es el evento MÁS IMPORTANTE del módulo Research.
    Solo cuando se emite este evento, el flujo de generación
    de Shorts puede continuar.

    Futuros consumers:
      - Scheduler: encola la generación del Short
      - Script Generator: activa la creación del guion
      - Notifications: avisa que ya hay contenido listo
    """
    topic_id: UUID
    title: str
    approved_at: datetime = field(default_factory=_utcnow)
    occurred_at: datetime = field(default_factory=_utcnow)


@dataclass(frozen=True)
class TopicRejected(DomainEvent):
    """
    Un topic fue rechazado por el usuario.

    Útil para:
      - Analytics: mejorar el scoring aprendiendo qué rechaza el usuario
      - Audit: registrar decisiones editoriales
    """
    topic_id: UUID
    title: str
    reason: str = ""
    rejected_at: datetime = field(default_factory=_utcnow)
    occurred_at: datetime = field(default_factory=_utcnow)
