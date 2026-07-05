"""
SyncPolicy Value Object — Configuración de sincronización para un Feed.

Define modo, intervalo, reintentos y timeout para la ejecución de fetch.
NO incluye lógica de timing (is_due, next_run) — es un VO de configuración
pura. El scheduler (Application Layer) decide cuándo ejecutar.

Modo PULL requiere ``interval_minutes`` obligatorio.
Modos PUSH, STREAM, MANUAL no requieren intervalo.
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.base.value_object import ValueObject

from ingestion.domain.exceptions import InvalidSyncPolicyError
from ingestion.domain.value_objects.sync_mode import SyncMode


@dataclass(frozen=True)
class SyncPolicy(ValueObject):
    """Política de sincronización para un Feed.

    Attributes:
        mode: Modo de sincronización (PULL, PUSH, STREAM, MANUAL).
        interval_minutes: Intervalo en minutos entre fetches (requerido para PULL).
        max_retries: Máximo de reintentos antes de pausar el Feed (default: 3).
        backoff_multiplier: Multiplicador para backoff exponencial (default: 2.0).
        max_backoff_minutes: Backoff máximo en minutos (default: 60).
        timeout_seconds: Timeout en segundos para cada fetch (default: 30).
        max_items_per_run: Máximo de items a obtener por ejecución (default: 100).

    Raises:
        InvalidSyncPolicyError: Si la configuración no es válida.
    """

    mode: SyncMode
    interval_minutes: int | None = None
    max_retries: int = 3
    backoff_multiplier: float = 2.0
    max_backoff_minutes: int = 60
    timeout_seconds: int = 30
    max_items_per_run: int = 100

    def __post_init__(self) -> None:
        """Validar la configuración en construcción."""
        self._validate_interval()
        self._validate_retry()
        self._validate_timeout()
        self._validate_backoff()
        self._validate_items_per_run()

    # ── Private validation methods ──

    def _validate_interval(self) -> None:
        """Validate interval_minutes requirement."""
        if self.mode == SyncMode.PULL and self.interval_minutes is None:
            raise InvalidSyncPolicyError(
                "PULL mode requires interval_minutes to be set"
            )

    def _validate_retry(self) -> None:
        """Validate max_retries >= 0."""
        if self.max_retries < 0:
            raise InvalidSyncPolicyError(
                f"max_retries must be >= 0, got {self.max_retries}"
            )

    def _validate_timeout(self) -> None:
        """Validate timeout_seconds > 0."""
        if self.timeout_seconds <= 0:
            raise InvalidSyncPolicyError(
                f"timeout_seconds must be > 0, got {self.timeout_seconds}"
            )

    def _validate_backoff(self) -> None:
        """Validate backoff settings."""
        if self.backoff_multiplier <= 1.0:
            raise InvalidSyncPolicyError(
                f"backoff_multiplier must be > 1.0, got {self.backoff_multiplier}"
            )

        if self.max_backoff_minutes <= 0:
            raise InvalidSyncPolicyError(
                f"max_backoff_minutes must be > 0, got {self.max_backoff_minutes}"
            )

    def _validate_items_per_run(self) -> None:
        """Validate max_items_per_run > 0."""
        if self.max_items_per_run <= 0:
            raise InvalidSyncPolicyError(
                f"max_items_per_run must be > 0, got {self.max_items_per_run}"
            )
