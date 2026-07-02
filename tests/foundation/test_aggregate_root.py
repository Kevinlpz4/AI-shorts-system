"""
Tests para AggregateRoot.

Cubre:
  - Construcción y herencia de Entity
  - Registro de eventos (DomainEvent)
  - Validación de tipo en register_event
  - Extracción y limpieza de eventos
  - Copia defensiva de eventos
  - Eventos no afectan igualdad ni hash
  - Representación (repr sin eventos)
  - Edge cases: múltiples ciclos, subclass con atributos, AR != Entity
"""

from dataclasses import dataclass
from uuid import UUID

import pytest

from foundation import AggregateRoot, DomainEvent, Entity, EntityId


# ══════════════════════════════════════════════
# Helpers concretos para testing
# ══════════════════════════════════════════════

@dataclass
class Order(AggregateRoot):
    """AggregateRoot concreto con atributo adicional."""
    total: float = 0.0


class MyAggregate(AggregateRoot):
    """AggregateRoot simple sin atributos adicionales."""
    pass


SAMPLE_UUID = UUID("12345678-1234-5678-1234-567812345678")
ANOTHER_UUID = UUID("87654321-4321-8765-4321-876543210987")


# ══════════════════════════════════════════════
# 1. Construcción y herencia
# ══════════════════════════════════════════════

class TestConstruction:
    def test_create_with_id(self):
        """AggregateRoot(id) debe construir correctamente."""
        eid = EntityId(value=SAMPLE_UUID)
        ar = AggregateRoot(id=eid)
        assert ar.id == eid

    def test_is_instance_of_entity(self):
        """AggregateRoot debe ser instancia de Entity."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        assert isinstance(ar, Entity)

    def test_is_instance_of_aggregate_root(self):
        """AggregateRoot debe ser instancia de sí mismo."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        assert isinstance(ar, AggregateRoot)

    def test_inherits_entity_equality(self):
        """Dos ARs con mismo id deben ser iguales."""
        eid = EntityId(value=SAMPLE_UUID)
        a = AggregateRoot(id=eid)
        b = AggregateRoot(id=eid)
        assert a == b

    def test_create_subclass_with_extra_fields(self):
        """Subclase con atributos adicionales debe construir."""
        eid = EntityId(value=SAMPLE_UUID)
        order = Order(id=eid, total=99.99)
        assert order.id == eid
        assert order.total == 99.99

    def test_not_equal_to_entity_same_id(self):
        """AggregateRoot != Entity aunque tengan el mismo id."""
        eid = EntityId(value=SAMPLE_UUID)
        ar = AggregateRoot(id=eid)
        entity = Entity(id=eid)
        assert ar != entity
        assert entity != ar

    def test_ar_does_not_know_infrastructure(self):
        """AggregateRoot NO debe tener métodos de infraestructura."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        # NO tiene estos métodos
        assert not hasattr(ar, "publish")
        assert not hasattr(ar, "dispatch")
        assert not hasattr(ar, "commit")
        assert not hasattr(ar, "send")


# ══════════════════════════════════════════════
# 2. Registro de eventos
# ══════════════════════════════════════════════

class TestEventRegistration:
    def test_register_event(self):
        """register_event debe almacenar un DomainEvent."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        ar.register_event(DomainEvent())
        assert len(ar.pull_events()) == 1

    def test_register_multiple_events(self):
        """Registrar múltiples DomainEvents debe almacenarlos todos."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        ar.register_event(DomainEvent())
        ar.register_event(DomainEvent())
        ar.register_event(DomainEvent())
        assert len(ar.pull_events()) == 3

    def test_register_rejects_non_domain_event(self):
        """register_event SOLO acepta DomainEvent — rechaza otros tipos."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        with pytest.raises(TypeError, match="DomainEvent"):
            ar.register_event("string_event")  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="DomainEvent"):
            ar.register_event(42)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="DomainEvent"):
            ar.register_event({})  # type: ignore[arg-type]


# ══════════════════════════════════════════════
# 3. Extracción y limpieza de eventos
# ══════════════════════════════════════════════

class TestEventExtraction:
    def test_pull_events_returns_events(self):
        """pull_events debe devolver los DomainEvents acumulados."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        e1 = DomainEvent()
        e2 = DomainEvent()
        ar.register_event(e1)
        ar.register_event(e2)
        events = ar.pull_events()
        assert len(events) == 2
        assert e1 in events
        assert e2 in events

    def test_pull_events_clears_list(self):
        """Después de pull_events, la lista interna debe estar vacía."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        ar.register_event(DomainEvent())
        ar.pull_events()
        assert len(ar.pull_events()) == 0

    def test_pull_events_without_register(self):
        """pull_events sin eventos debe devolver lista vacía."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        assert ar.pull_events() == []

    def test_multiple_register_and_pull_cycles(self):
        """Ciclos register → pull → register → pull deben funcionar."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))

        # Primer ciclo
        ar.register_event(DomainEvent())
        assert len(ar.pull_events()) == 1
        assert len(ar.pull_events()) == 0  # ya vacío

        # Segundo ciclo
        e1 = DomainEvent()
        e2 = DomainEvent()
        ar.register_event(e1)
        ar.register_event(e2)
        events = ar.pull_events()
        assert len(events) == 2
        assert e1 in events
        assert e2 in events

        # Vacío nuevamente
        assert len(ar.pull_events()) == 0

    def test_pull_events_empties_internal_collection(self):
        """Verificar que _events está vacío después de pull."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        ar.register_event(DomainEvent())
        ar.pull_events()
        assert len(ar._events) == 0  # type: ignore[arg-type]


# ══════════════════════════════════════════════
# 4. Copia defensiva de eventos
# ══════════════════════════════════════════════

class TestDefensiveCopy:
    def test_pull_returns_new_list(self):
        """La lista devuelta debe ser un objeto NUEVO, no la referencia interna."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        ar.register_event(DomainEvent())
        pulled = ar.pull_events()
        assert pulled is not ar._events

    def test_mutating_pulled_events_does_not_affect_internal(self):
        """Mutar la lista devuelta NO debe afectar la colección interna."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        ar.register_event(DomainEvent())
        ar.register_event(DomainEvent())

        pulled = ar.pull_events()
        pulled.append(DomainEvent())  # type: ignore[arg-type]

        # La colección interna ya fue limpiada
        assert len(ar._events) == 0  # type: ignore[arg-type]

    def test_pulled_events_are_frozen_domain_events(self):
        """Los eventos extraídos son DomainEvent frozen."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        ar.register_event(DomainEvent())
        pulled = ar.pull_events()
        assert len(pulled) == 1
        assert isinstance(pulled[0], DomainEvent)
        assert pulled[0].event_name == "DomainEvent"


# ══════════════════════════════════════════════
# 5. Eventos no afectan igualdad
# ══════════════════════════════════════════════

class TestEventsDoNotAffectEquality:
    def test_events_not_in_equality(self):
        """ARs con mismo ID pero diferentes eventos deben ser iguales."""
        eid = EntityId(value=SAMPLE_UUID)
        a = AggregateRoot(id=eid)
        b = AggregateRoot(id=eid)

        a.register_event(DomainEvent())
        b.register_event(DomainEvent())

        assert a == b

    def test_events_not_in_hash(self):
        """Eventos diferentes no deben afectar el hash."""
        eid = EntityId(value=SAMPLE_UUID)
        a = AggregateRoot(id=eid)
        b = AggregateRoot(id=eid)

        a.register_event(DomainEvent())
        b.register_event(DomainEvent())

        assert hash(a) == hash(b)

    def test_hash_equals_entity_id_hash(self):
        """El hash del AR debe ser el hash de su EntityId."""
        eid = EntityId(value=SAMPLE_UUID)
        ar = AggregateRoot(id=eid)
        assert hash(ar) == hash(eid)

    def test_ar_equality_in_set(self):
        """ARs con mismo ID deben deduplicarse en set."""
        eid = EntityId(value=SAMPLE_UUID)
        a = AggregateRoot(id=eid)
        b = AggregateRoot(id=eid)
        a.register_event(DomainEvent())
        s = {a, b}
        assert len(s) == 1


# ══════════════════════════════════════════════
# 6. Representación
# ══════════════════════════════════════════════

class TestRepresentation:
    def test_repr_does_not_include_events(self):
        """repr() NO debe incluir los eventos."""
        ar = AggregateRoot(id=EntityId(value=SAMPLE_UUID))
        ar.register_event(DomainEvent())
        representation = repr(ar)
        assert "_events" not in representation
        assert "DomainEvent" not in representation

    def test_repr_includes_id(self):
        """repr() debe incluir el id."""
        eid = EntityId(value=SAMPLE_UUID)
        ar = AggregateRoot(id=eid)
        assert str(eid) in repr(ar)
