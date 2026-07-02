"""
Tests del Event System (Sprint 2.4).

Cubre: DomainEvent, IntegrationEvent.

~25 tests organizados en 5 grupos:

    - TestDomainEventCreation  (5) — Construcción de DomainEvent
    - TestIntegrationEventCreation (6) — Construcción de IntegrationEvent
    - TestInmutabilidad         (4) — Frozen en ambos tipos
    - TestIgualdad              (4) — Igualdad estructural y hash
    - TestEdgeCases             (6) — Casos borde
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from datetime import datetime, timezone

from foundation import DomainEvent, IntegrationEvent

# ══════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════

SAMPLE_UUID = UUID("12345678-1234-5678-1234-567812345678")
ANOTHER_UUID = UUID("87654321-4321-8765-4321-876543210987")
FROZEN_NOW = datetime(2026, 7, 2, 0, 0, 0, tzinfo=timezone.utc)


# ══════════════════════════════════════════════
# 1. DomainEvent — Creación
# ══════════════════════════════════════════════


class TestDomainEventCreation:
    """Test de construcción de DomainEvent."""

    def test_create_default(self):
        """DomainEvent() construye con valores default."""
        event = DomainEvent()
        assert isinstance(event.event_id, UUID)
        assert event.event_version == 1
        assert event.occurred_at is not None

    def test_event_name_property(self):
        """event_name retorna el nombre de la clase."""
        event = DomainEvent()
        assert event.event_name == "DomainEvent"

    def test_event_name_in_subclass(self):
        """event_name en subclase retorna el nombre de la subclase."""
        from dataclasses import dataclass, field
        from uuid import uuid4

        @dataclass(frozen=True)
        class TopicDiscovered(DomainEvent):
            topic_id: UUID = field(default_factory=uuid4)

        event = TopicDiscovered()
        assert event.event_name == "TopicDiscovered"

    def test_custom_event_id(self):
        """Se puede pasar un event_id custom."""
        event = DomainEvent(event_id=SAMPLE_UUID)
        assert event.event_id == SAMPLE_UUID

    def test_custom_event_version(self):
        """Se puede pasar un event_version custom."""
        event = DomainEvent(event_version=2)
        assert event.event_version == 2


# ══════════════════════════════════════════════
# 2. IntegrationEvent — Creación
# ══════════════════════════════════════════════


class TestIntegrationEventCreation:
    """Test de construcción de IntegrationEvent."""

    def test_create_default(self):
        """IntegrationEvent() construye con valores default."""
        event = IntegrationEvent()
        assert isinstance(event.event_id, UUID)
        assert event.event_version == 1
        assert event.source_boundary == ""
        assert event.correlation_id is None
        assert event.causation_id is None
        assert event.occurred_at is not None

    def test_event_name_property(self):
        """event_name retorna el nombre de la clase."""
        event = IntegrationEvent()
        assert event.event_name == "IntegrationEvent"

    def test_with_source_boundary(self):
        """source_boundary se puede setear."""
        event = IntegrationEvent(source_boundary="research")
        assert event.source_boundary == "research"

    def test_with_correlation_id(self):
        """correlation_id se puede setear."""
        event = IntegrationEvent(correlation_id="corr-123")
        assert event.correlation_id == "corr-123"

    def test_with_causation_id(self):
        """causation_id se puede setear."""
        event = IntegrationEvent(causation_id=SAMPLE_UUID)
        assert event.causation_id == SAMPLE_UUID

    def test_event_name_in_subclass(self):
        """event_name en subclase retorna el nombre de la subclase."""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class TopicPublished(IntegrationEvent):
            source_boundary: str = "research"

        event = TopicPublished()
        assert event.event_name == "TopicPublished"


# ══════════════════════════════════════════════
# 3. Inmutabilidad
# ══════════════════════════════════════════════


class TestInmutabilidad:
    """Test de inmutabilidad (frozen=True)."""

    def test_domain_event_frozen(self):
        """No se puede mutar un DomainEvent."""
        event = DomainEvent()
        with pytest.raises(FrozenInstanceError):
            event.event_id = SAMPLE_UUID  # type: ignore[misc]

    def test_integration_event_frozen(self):
        """No se puede mutar un IntegrationEvent."""
        event = IntegrationEvent()
        with pytest.raises(FrozenInstanceError):
            event.event_id = SAMPLE_UUID  # type: ignore[misc]

    def test_event_name_is_property_not_field(self):
        """event_name NO es un campo — no se puede setear."""
        event = DomainEvent()
        with pytest.raises(AttributeError):
            event.event_name = "CustomName"  # type: ignore[attr-defined]

    def test_integration_event_name_is_property_not_field(self):
        """event_name NO es un campo en IntegrationEvent."""
        event = IntegrationEvent()
        with pytest.raises(AttributeError):
            event.event_name = "CustomName"  # type: ignore[attr-defined]


# ══════════════════════════════════════════════
# 4. Igualdad y Hash
# ══════════════════════════════════════════════


class TestIgualdad:
    """Test de igualdad estructural y hash."""

    def test_domain_event_equality(self):
        """Dos DomainEvent con mismos atributos son iguales."""
        a = DomainEvent(event_id=SAMPLE_UUID, event_version=1, occurred_at=FROZEN_NOW)
        b = DomainEvent(event_id=SAMPLE_UUID, event_version=1, occurred_at=FROZEN_NOW)
        assert a == b
        assert hash(a) == hash(b)

    def test_domain_event_inequality(self):
        """Dos DomainEvent con diferente event_id NO son iguales."""
        a = DomainEvent(event_id=SAMPLE_UUID, occurred_at=FROZEN_NOW)
        b = DomainEvent(event_id=ANOTHER_UUID, occurred_at=FROZEN_NOW)
        assert a != b

    def test_integration_event_equality(self):
        """Dos IntegrationEvent con mismos atributos son iguales."""
        a = IntegrationEvent(event_id=SAMPLE_UUID, source_boundary="test", occurred_at=FROZEN_NOW)
        b = IntegrationEvent(event_id=SAMPLE_UUID, source_boundary="test", occurred_at=FROZEN_NOW)
        assert a == b
        assert hash(a) == hash(b)

    def test_integration_event_inequality(self):
        """Dos IntegrationEvent con diferente event_id NO son iguales."""
        a = IntegrationEvent(event_id=SAMPLE_UUID, occurred_at=FROZEN_NOW)
        b = IntegrationEvent(event_id=ANOTHER_UUID, occurred_at=FROZEN_NOW)
        assert a != b


# ══════════════════════════════════════════════
# 5. Edge Cases
# ══════════════════════════════════════════════


class TestEdgeCases:
    """Test de casos borde."""

    def test_domain_event_is_not_exception(self):
        """DomainEvent NO es una excepción."""
        event = DomainEvent()
        assert not isinstance(event, Exception)
        assert not isinstance(event, BaseException)

    def test_integration_event_is_not_exception(self):
        """IntegrationEvent NO es una excepción."""
        event = IntegrationEvent()
        assert not isinstance(event, Exception)
        assert not isinstance(event, BaseException)

    def test_domain_event_in_set(self):
        """DomainEvent es hashable y funciona en sets."""
        a = DomainEvent(event_id=SAMPLE_UUID, occurred_at=FROZEN_NOW)
        b = DomainEvent(event_id=SAMPLE_UUID, occurred_at=FROZEN_NOW)
        s = {a, b}
        assert len(s) == 1  # deduplicación por igualdad

    def test_integration_event_in_dict(self):
        """IntegrationEvent funciona como key de dict."""
        key = IntegrationEvent(event_id=SAMPLE_UUID, source_boundary="test", occurred_at=FROZEN_NOW)
        d = {key: "value"}
        assert d[IntegrationEvent(event_id=SAMPLE_UUID, source_boundary="test", occurred_at=FROZEN_NOW)] == "value"

    def test_subclass_with_extra_fields(self):
        """Subclase con campos adicionales funciona correctamente."""
        from dataclasses import dataclass, field
        from uuid import uuid4

        @dataclass(frozen=True)
        class TopicDiscovered(DomainEvent):
            topic_id: UUID = field(default_factory=uuid4)
            title: str = ""

        event = TopicDiscovered(title="AI Trends")
        assert event.event_name == "TopicDiscovered"
        assert event.title == "AI Trends"
        assert isinstance(event.topic_id, UUID)

    def test_subclass_preserves_parent_behavior(self):
        """Subclase mantiene event_id, event_version, occurred_at."""
        from dataclasses import dataclass, field
        from uuid import uuid4

        @dataclass(frozen=True)
        class FeedAdded(DomainEvent):
            feed_id: UUID = field(default_factory=uuid4)

        event = FeedAdded(event_version=2)
        assert event.event_name == "FeedAdded"
        assert isinstance(event.event_id, UUID)
        assert event.event_version == 2
        assert event.occurred_at is not None
