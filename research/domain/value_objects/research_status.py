"""
ResearchStatus — Estados del ciclo de vida de un ResearchTopic
===============================================================
FOUND          → Acaba de ser descubierto por una fuente
PENDING_REVIEW → Esperando aprobación humana (estado por defecto después de dedup + scoring)
APPROVED       → El usuario aprobó el topic para generar contenido
REJECTED       → El usuario rechazó el topic

Transiciones válidas:
  FOUND → PENDING_REVIEW (automático, después de procesar)
  PENDING_REVIEW → APPROVED (manual, acción del usuario)
  PENDING_REVIEW → REJECTED (manual, acción del usuario)

  Cualquier otra transición → ResearchAlreadyReviewedError
"""

from enum import Enum


class ResearchStatus(Enum):
    """Estados del ciclo de vida de un topic de investigación."""

    FOUND = "found"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"

    @property
    def is_terminal(self) -> bool:
        """Estados terminales: no se pueden modificar."""
        return self in (ResearchStatus.APPROVED, ResearchStatus.REJECTED)

    @property
    def is_reviewable(self) -> bool:
        """Solo los topics en PENDING_REVIEW pueden ser aprobados/rechazados."""
        return self == ResearchStatus.PENDING_REVIEW

    @classmethod
    def default(cls) -> "ResearchStatus":
        """
        Estado por defecto al crear un topic.
        Los topics van directamente a PENDING_REVIEW para aprobación humana.
        """
        return cls.PENDING_REVIEW
