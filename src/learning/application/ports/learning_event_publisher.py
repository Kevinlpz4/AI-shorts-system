"""
LearningEventPublisher Port — Publicación de eventos específicos del Learning BC.

Define el contrato para publicar eventos tipados del Learning BC.
A diferencia de ``EventPublisher`` (genérico), este port expone
métodos específicos por tipo de evento para mayor seguridad de tipos.

Uso::

    publisher.publish_feedback_captured(event)
    publisher.publish_signal_aggregated(event)
"""

from __future__ import annotations

from typing import Protocol

from learning.domain.events.learning_events import (
    DatasetGenerated,
    FeedbackCaptured,
    LearningModelUpdated,
    ScoreAdjusted,
    SignalAggregated,
)


class LearningEventPublisher(Protocol):
    """Publica eventos específicos del Learning BC.

    Responsabilidades:
        - publish_feedback_captured(): Publicar evento de feedback capturado.
        - publish_signal_aggregated(): Publicar evento de señal agregada.
        - publish_score_adjusted(): Publicar evento de ajuste de scores.
        - publish_dataset_generated(): Publicar evento de dataset generado.
        - publish_learning_model_updated(): Publicar evento de modelo actualizado.

    NOTA: Este port es complementario a ``EventPublisher``.
    ``EventPublisher`` se usa para publicación genérica post-commit.
    ``LearningEventPublisher`` se usa cuando se necesita un routing
    específico por tipo de evento (e.g., different queues per event type).
    """

    def publish_feedback_captured(self, event: FeedbackCaptured) -> None:
        """Publica un evento FeedbackCaptured.

        Args:
            event: El evento de feedback capturado.
        """
        ...

    def publish_signal_aggregated(self, event: SignalAggregated) -> None:
        """Publica un evento SignalAggregated.

        Args:
            event: El evento de señal agregada.
        """
        ...

    def publish_score_adjusted(self, event: ScoreAdjusted) -> None:
        """Publica un evento ScoreAdjusted.

        Args:
            event: El evento de ajuste de scores.
        """
        ...

    def publish_dataset_generated(self, event: DatasetGenerated) -> None:
        """Publica un evento DatasetGenerated.

        Args:
            event: El evento de dataset generado.
        """
        ...

    def publish_learning_model_updated(self, event: LearningModelUpdated) -> None:
        """Publica un evento LearningModelUpdated.

        Args:
            event: El evento de modelo actualizado.
        """
        ...
