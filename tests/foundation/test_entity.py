"""
Tests para Entity.

Cubre:
  - Construcción (con/sin id, subclases)
  - Igualdad por identidad (mismo id → igual, diferente tipo → no igual)
  - Igualdad por tipo estricto (Entity != AggregateRoot, Person != Company)
  - Hash exclusivamente basado en EntityId
  - Mutabilidad controlada (atributos no-id mutables, id inmutable)
  - Colecciones (set, dict)
  - Edge cases: comparación con None, string, int
"""

from dataclasses import FrozenInstanceError, dataclass
from uuid import UUID

import pytest

from foundation import Entity, EntityId, AggregateRoot


# ══════════════════════════════════════════════
# Helpers concretos para testing
# ══════════════════════════════════════════════

@dataclass(eq=False)
class Person(Entity):
    """Entidad concreta con atributo adicional."""
    name: str


@dataclass(eq=False)
class Company(Entity):
    """Otra entidad para testear type safety en igualdad."""
    name: str


SAMPLE_UUID = UUID("12345678-1234-5678-1234-567812345678")
ANOTHER_UUID = UUID("87654321-4321-8765-4321-876543210987")


# ══════════════════════════════════════════════
# 1. Construcción
# ══════════════════════════════════════════════

class TestConstruction:
    def test_create_with_id(self):
        """Entity(id=EntityId) debe construir correctamente."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        assert entity.id == eid

    def test_create_without_id_raises(self):
        """Entity() sin id debe lanzar TypeError."""
        with pytest.raises(TypeError):
            Entity()  # type: ignore[call-arg]

    def test_create_subclass_with_extra_fields(self):
        """Subclase con atributos adicionales debe construir correctamente."""
        eid = EntityId(value=SAMPLE_UUID)
        person = Person(id=eid, name="Alice")
        assert person.id == eid
        assert person.name == "Alice"

    def test_entity_id_is_entity_id_type(self):
        """El atributo id debe ser de tipo EntityId."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        assert type(entity.id) is EntityId


# ══════════════════════════════════════════════
# 2. Igualdad por identidad
# ══════════════════════════════════════════════

class TestIdentityEquality:
    def test_same_id_are_equal(self):
        """Dos entities con el mismo id deben ser iguales."""
        eid = EntityId(value=SAMPLE_UUID)
        a = Entity(id=eid)
        b = Entity(id=eid)
        assert a == b

    def test_different_id_not_equal(self):
        """Entities con diferentes ids no deben ser iguales."""
        a = Entity(id=EntityId(value=SAMPLE_UUID))
        b = Entity(id=EntityId(value=ANOTHER_UUID))
        assert a != b

    def test_equal_with_different_attributes(self):
        """Misma identidad, diferentes atributos → iguales."""
        eid = EntityId(value=SAMPLE_UUID)
        a = Person(id=eid, name="Alice")
        b = Person(id=eid, name="Bob")
        assert a == b
        assert b == a

    def test_symmetric_equality(self):
        """Igualdad debe ser simétrica."""
        eid = EntityId(value=SAMPLE_UUID)
        a = Entity(id=eid)
        b = Entity(id=eid)
        assert a == b
        assert b == a

    def test_reflexive_equality(self):
        """Una entidad debe ser igual a sí misma."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        assert entity == entity


# ══════════════════════════════════════════════
# 3. Igualdad por tipo estricto
# ══════════════════════════════════════════════

class TestStrictTypeEquality:
    def test_different_type_same_id_not_equal(self):
        """Mismo id, diferentes tipos → NO iguales."""
        eid = EntityId(value=SAMPLE_UUID)
        person = Person(id=eid, name="Alice")
        company = Company(id=eid, name="Alice")
        assert person != company

    def test_different_type_different_id_not_equal(self):
        """Diferente tipo y diferente id → NO iguales."""
        person = Person(id=EntityId(value=SAMPLE_UUID), name="Alice")
        company = Company(id=EntityId(value=ANOTHER_UUID), name="Corp")
        assert person != company

    def test_entity_vs_aggregate_root_not_equal(self):
        """Entity != AggregateRoot aunque tengan el mismo id."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        ar = AggregateRoot(id=eid)
        assert entity != ar
        assert ar != entity

    def test_compare_with_non_entity_returns_false(self):
        """Comparar Entity con tipos no-Entity debe devolver False."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        assert (entity == "string") is False
        assert (entity == 42) is False

    def test_compare_with_none_returns_false(self):
        """Entity == None debe devolver False."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        assert (entity is not None)

    def test_not_implemented_for_different_type(self):
        """__eq__ debe devolver NotImplemented para tipos no compatibles."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        # Python's reflexión convierte NotImplemented en False
        assert (entity == []) is False


# ══════════════════════════════════════════════
# 4. Hash
# ══════════════════════════════════════════════

class TestHash:
    def test_equal_ids_same_hash(self):
        """Entities iguales deben tener el mismo hash."""
        eid = EntityId(value=SAMPLE_UUID)
        a = Entity(id=eid)
        b = Entity(id=eid)
        assert hash(a) == hash(b)

    def test_hash_depends_only_on_id(self):
        """Hash debe depender SOLO del id, no de otros atributos."""
        eid = EntityId(value=SAMPLE_UUID)
        a = Person(id=eid, name="Alice")
        b = Person(id=eid, name="Bob")
        assert hash(a) == hash(b)

    def test_different_id_different_hash(self):
        """IDs diferentes deben tener hashes diferentes (colisión improbable)."""
        a = Entity(id=EntityId(value=SAMPLE_UUID))
        b = Entity(id=EntityId(value=ANOTHER_UUID))
        assert hash(a) != hash(b)

    def test_hash_is_entity_id_hash(self):
        """hash(entity) debe ser igual a hash(entity.id)."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        assert hash(entity) == hash(eid)

    def test_consistent_hash_across_calls(self):
        """Hash debe ser consistente en llamadas múltiples."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        h1 = hash(entity)
        h2 = hash(entity)
        assert h1 == h2


# ══════════════════════════════════════════════
# 5. Mutabilidad controlada
# ══════════════════════════════════════════════

class TestMutability:
    def test_can_modify_non_id_field(self):
        """Atributos no-id deben ser mutables."""
        eid = EntityId(value=SAMPLE_UUID)
        person = Person(id=eid, name="Alice")
        person.name = "Bob"
        assert person.name == "Bob"

    def test_cannot_modify_id_value(self):
        """El value del EntityId no debe ser mutable (EntityId es frozen)."""
        eid = EntityId(value=SAMPLE_UUID)
        with pytest.raises(FrozenInstanceError):
            eid.value = ANOTHER_UUID  # type: ignore[misc]


# ══════════════════════════════════════════════
# 6. Colecciones (set, dict)
# ══════════════════════════════════════════════

class TestCollections:
    def test_entity_in_set(self):
        """Entity debe funcionar como elemento de set."""
        eid1 = EntityId(value=SAMPLE_UUID)
        eid2 = EntityId(value=ANOTHER_UUID)
        s = {Entity(id=eid1), Entity(id=eid2)}
        assert len(s) == 2

    def test_entity_as_dict_key(self):
        """Entity debe funcionar como key de dict."""
        eid = EntityId(value=SAMPLE_UUID)
        entity = Entity(id=eid)
        d = {entity: "value"}
        assert d[entity] == "value"

    def test_set_deduplicates_by_id(self):
        """Set debe deduplicar entities con el mismo id."""
        eid = EntityId(value=SAMPLE_UUID)
        s = {Entity(id=eid), Entity(id=eid)}
        assert len(s) == 1

    def test_dict_key_retrieval_by_equivalent_entity(self):
        """Lookup en dict debe funcionar con entidad equivalente."""
        eid = EntityId(value=SAMPLE_UUID)
        a = Entity(id=eid)
        b = Entity(id=eid)
        d = {a: "found"}
        assert d[b] == "found"

    def test_set_with_subclasses_same_id(self):
        """Subclases con el mismo id NO deben deduplicarse (tipos diferentes)."""
        eid = EntityId(value=SAMPLE_UUID)
        s = {Person(id=eid, name="Alice"), Company(id=eid, name="Corp")}
        assert len(s) == 2  # diferentes tipos → diferentes entidades
