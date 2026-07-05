"""
Domain Events for the Ingestion Bounded Context.

All events inherit from ``DomainEvent`` (Foundation) and are ``@dataclass(frozen=True)``.

Events:
  - RawArticleCollected: Emitted by Feed when new articles are collected.
  - SourceEnabled: Emitted by NewsSource when enabled.
  - SourceDisabled: Emitted by NewsSource when disabled.

NOTE: Child fields use a sentinel default (MISSING) to work around Python's
dataclass field ordering requirement (fields with defaults must come after
fields without defaults in inheritance). The sentinel is validated in
``__post_init__``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from foundation.events.domain_event import DomainEvent

from ingestion.domain.entities.ids import FeedId, SourceId


class _MISSING_TYPE:
    """Sentinel type for required dataclass fields with defaults."""

    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False


MISSING: Any = _MISSING_TYPE()


@dataclass(frozen=True)
class RawArticleCollected(DomainEvent):
    """Indica que uno o más RawArticles han sido recolectados exitosamente.

    Emitido por Feed.record_collection() cuando count > 0 después de
    deduplicación.

    Attributes:
        feed_id: Feed del que se recolectaron los artículos.
        batch_id: UUID del batch al que pertenecen los artículos.
        count: Cantidad de artículos nuevos (post-dedup).
        collected_at: Momento exacto de la colección.
    """

    feed_id: FeedId = field(default=MISSING)  # type: ignore[assignment]
    batch_id: UUID = field(default=MISSING)  # type: ignore[assignment]
    count: int = field(default=MISSING)
    collected_at: datetime = field(default=MISSING)

    def __post_init__(self) -> None:
        """Validate required fields were provided."""
        if isinstance(self.feed_id, _MISSING_TYPE):
            raise TypeError("RawArticleCollected.feed_id is required")
        if isinstance(self.batch_id, _MISSING_TYPE):
            raise TypeError("RawArticleCollected.batch_id is required")
        if isinstance(self.count, _MISSING_TYPE):
            raise TypeError("RawArticleCollected.count is required")
        if isinstance(self.collected_at, _MISSING_TYPE):
            raise TypeError("RawArticleCollected.collected_at is required")
        if self.count < 0:
            raise ValueError("count must be >= 0")


@dataclass(frozen=True)
class SourceEnabled(DomainEvent):
    """Indica que un NewsSource ha sido habilitado para ingesta.

    Emitido por NewsSource.enable().

    Attributes:
        source_id: NewsSource que se habilitó.
        enabled_at: Momento exacto de la habilitación.
    """

    source_id: SourceId = field(default=MISSING)  # type: ignore[assignment]
    enabled_at: datetime = field(default=MISSING)

    def __post_init__(self) -> None:
        """Validate required fields were provided."""
        if isinstance(self.source_id, _MISSING_TYPE):
            raise TypeError("SourceEnabled.source_id is required")
        if isinstance(self.enabled_at, _MISSING_TYPE):
            raise TypeError("SourceEnabled.enabled_at is required")


@dataclass(frozen=True)
class SourceDisabled(DomainEvent):
    """Indica que un NewsSource ha sido deshabilitado.

    Emitido por NewsSource.disable(reason).

    Attributes:
        source_id: NewsSource que se deshabilitó.
        reason: Razón de la deshabilitación.
        disabled_at: Momento exacto de la deshabilitación.
    """

    source_id: SourceId = field(default=MISSING)  # type: ignore[assignment]
    reason: str = field(default=MISSING)  # type: ignore[assignment]
    disabled_at: datetime = field(default=MISSING)

    def __post_init__(self) -> None:
        """Validate required fields were provided."""
        if isinstance(self.source_id, _MISSING_TYPE):
            raise TypeError("SourceDisabled.source_id is required")
        if isinstance(self.reason, _MISSING_TYPE):
            raise TypeError("SourceDisabled.reason is required")
        if isinstance(self.disabled_at, _MISSING_TYPE):
            raise TypeError("SourceDisabled.disabled_at is required")
