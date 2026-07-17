"""
Repository Ports for the Learning Bounded Context.

All repositories are ``Protocol`` (structural typing). Any class that implements
the methods with the correct signatures is automatically a valid repository.

Principles:
  1. Protocols, not ABCs.
  2. No technology mentioned (no SQL, no Redis, no async).
  3. Methods use domain types (entity objects, VOs, IDs), not primitives.
  4. ``Result[T]`` for operations that can fail (find_by_*).
  5. ``list[T]`` for operations that may return empty.
  6. ``int`` for count operations.
  7. Each Aggregate Root has its own repository.
  8. ``save()`` receives the full entity (no partial updates).
"""
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from foundation.result.result import Result

from learning.domain.entities.feedback_record import FeedbackRecord
from learning.domain.entities.ids import (
    FeedbackId,
    LearningModelId,
    LearningSignalId,
    SourceQualityId,
)
from learning.domain.entities.learning_model import LearningModel
from learning.domain.entities.learning_signal import LearningSignal
from learning.domain.entities.source_quality import SourceQualityProfile
from learning.domain.value_objects.decision_type import DecisionType
from learning.domain.value_objects.signal_type import SignalType


class FeedbackRepository(Protocol):
    """Puerto de persistencia para FeedbackRecord (Aggregate Root, Inmutable)."""

    def save(self, feedback: FeedbackRecord) -> None:
        """Persiste un FeedbackRecord (siempre es creación, nunca actualización).

        Puede fallar con DUPLICATE_FEEDBACK si ya existe.
        """
        ...

    def find_by_id(self, id: FeedbackId) -> Result[FeedbackRecord]:
        """Busca un FeedbackRecord por su identidad única.

        Returns:
            Ok(FeedbackRecord) si se encuentra.
            Error(FEEDBACK_NOT_FOUND) si no existe.
        """
        ...

    def find_by_topic_id(self, topic_id: str) -> list[FeedbackRecord]:
        """Retorna todos los FeedbackRecords para un topic."""
        ...

    def find_by_source(self, source_name: str) -> list[FeedbackRecord]:
        """Retorna todos los FeedbackRecords de un source."""
        ...

    def find_all_in_window(
        self, start: datetime, end: datetime
    ) -> list[FeedbackRecord]:
        """Retorna todos los FeedbackRecords dentro de un rango de tiempo."""
        ...

    def count_by_decision(self, decision: DecisionType) -> int:
        """Cuenta FeedbackRecords con un tipo de decisión dado."""
        ...


class LearningSignalRepository(Protocol):
    """Puerto de persistencia para LearningSignal (Aggregate Root)."""

    def save(self, signal: LearningSignal) -> None:
        """Persiste un LearningSignal (crea o actualiza)."""
        ...

    def save_batch(self, signals: list[LearningSignal]) -> None:
        """Persiste múltiples LearningSignals en una operación atómica."""
        ...

    def find_by_id(self, id: LearningSignalId) -> Result[LearningSignal]:
        """Busca un LearningSignal por su identidad única.

        Returns:
            Ok(LearningSignal) si se encuentra.
            Error(SIGNAL_NOT_FOUND) si no existe.
        """
        ...

    def find_by_type_and_dimension(
        self, signal_type: SignalType, dimension: str
    ) -> Result[LearningSignal]:
        """Busca un LearningSignal por tipo y dimensión.

        Returns:
            Ok(LearningSignal) si se encuentra.
            Error(SIGNAL_NOT_FOUND) si no existe.
        """
        ...

    def find_by_window(
        self, start: datetime, end: datetime
    ) -> list[LearningSignal]:
        """Retorna señales dentro de un rango de tiempo."""
        ...

    def find_all_active(self) -> list[LearningSignal]:
        """Retorna todas las señales con sample_size > 0."""
        ...


class SourceQualityRepository(Protocol):
    """Puerto de persistencia para SourceQualityProfile (Aggregate Root)."""

    def save(self, profile: SourceQualityProfile) -> None:
        """Persiste un SourceQualityProfile (crea o actualiza)."""
        ...

    def find_by_id(self, id: SourceQualityId) -> Result[SourceQualityProfile]:
        """Busca un SourceQualityProfile por su identidad única.

        Returns:
            Ok(SourceQualityProfile) si se encuentra.
            Error(SOURCE_QUALITY_NOT_FOUND) si no existe.
        """
        ...

    def find_by_source_name(
        self, source_name: str
    ) -> Result[SourceQualityProfile]:
        """Busca un SourceQualityProfile por nombre de source.

        Returns:
            Ok(SourceQualityProfile) si se encuentra.
            Error(SOURCE_QUALITY_NOT_FOUND) si no existe.
        """
        ...

    def find_all_active(self) -> list[SourceQualityProfile]:
        """Retorna todos los perfiles con total_decisions > 0."""
        ...

    def exists_by_source_name(self, source_name: str) -> bool:
        """Verifica si existe un perfil para el source dado."""
        ...


class LearningModelRepository(Protocol):
    """Puerto de persistencia para LearningModel (Aggregate Root)."""

    def save(self, model: LearningModel) -> None:
        """Persiste un LearningModel (crea o actualiza)."""
        ...

    def find_by_id(self, id: LearningModelId) -> Result[LearningModel]:
        """Busca un LearningModel por su identidad única.

        Returns:
            Ok(LearningModel) si se encuentra.
            Error(MODEL_NOT_FOUND) si no existe.
        """
        ...

    def find_current(self) -> Result[LearningModel]:
        """Busca el LearningModel actual (versión más reciente).

        Returns:
            Ok(LearningModel) si existe alguno.
            Error(MODEL_NOT_FOUND) si no hay modelos.
        """
        ...

    def find_by_version(
        self, version_str: str
    ) -> Result[LearningModel]:
        """Busca un LearningModel por string de versión (e.g., '1.2.3').

        Returns:
            Ok(LearningModel) si se encuentra.
            Error(MODEL_NOT_FOUND) si no existe.
        """
        ...
