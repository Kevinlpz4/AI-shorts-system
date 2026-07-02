"""
Tests para EntityId y FoundationEncoder.

Cubre todas las categorías del Sprint 2.1 Spec:
  - Construcción
  - Igualdad (incluyendo type safety)
  - Serialización (str, repr, from_string)
  - JSON (FoundationEncoder)
  - Colecciones (set, dict)
  - Pickle
  - Copy (shallow + deep)
  - Inmutabilidad
"""

import copy
import json
import pickle
from dataclasses import FrozenInstanceError
from uuid import UUID

import pytest

from foundation import EntityId, FoundationEncoder

# ──────────────────────────────────────────────
# Fixtures y helpers
# ──────────────────────────────────────────────

SAMPLE_UUID = UUID("12345678-1234-5678-1234-567812345678")
ANOTHER_UUID = UUID("87654321-4321-8765-4321-876543210987")


class AId(EntityId):
    """Subtipo concreto para testear type safety en igualdad."""
    pass


class BId(EntityId):
    """Otro subtipo concreto para testear type safety."""
    pass


# ──────────────────────────────────────────────
# 1. Construcción
# ──────────────────────────────────────────────

class TestConstruction:
    def test_create_with_default_generates_uuid(self):
        """EntityId() debe generar un UUID automáticamente."""
        eid = EntityId()
        assert isinstance(eid.value, UUID)

    def test_create_with_specific_uuid(self):
        """EntityId(value=u) debe usar exactamente ese UUID."""
        eid = EntityId(value=SAMPLE_UUID)
        assert eid.value == SAMPLE_UUID

    def test_value_is_uuid_not_string(self):
        """La propiedad value debe ser uuid.UUID, no string."""
        eid = EntityId(value=SAMPLE_UUID)
        assert type(eid.value) is UUID

    def test_new_factory_method(self):
        """EntityId.new() debe crear un ID con UUID válido."""
        eid = EntityId.new()
        assert isinstance(eid.value, UUID)

    def test_new_returns_unique_values(self):
        """Llamadas consecutivas a new() deben producir IDs diferentes."""
        a = EntityId.new()
        b = EntityId.new()
        assert a != b
        assert a.value != b.value

    def test_create_with_none_raises_type_error(self):
        """EntityId(value=None) debe lanzar TypeError."""
        with pytest.raises(TypeError):
            EntityId(value=None)

    def test_create_with_int_raises_type_error(self):
        """EntityId(value=123) debe lanzar TypeError."""
        with pytest.raises(TypeError):
            EntityId(value=123)

    def test_create_with_float_raises_type_error(self):
        """EntityId(value=3.14) debe lanzar TypeError."""
        with pytest.raises(TypeError):
            EntityId(value=3.14)

    def test_create_with_list_raises_type_error(self):
        """EntityId(value=[1,2,3]) debe lanzar TypeError."""
        with pytest.raises(TypeError):
            EntityId(value=[1, 2, 3])

    def test_create_with_string_raises_type_error(self):
        """EntityId(value='...str...') debe lanzar TypeError.
        Para crear desde string, usar EntityId.from_string()."""
        with pytest.raises(TypeError):
            EntityId(value="12345678-1234-5678-1234-567812345678")

    def test_create_subclass_with_default(self):
        """Una subclase sin fields debe poder crearse con default."""
        eid = AId()
        assert isinstance(eid, AId)
        assert isinstance(eid.value, UUID)

    def test_create_subclass_with_specific_value(self):
        """Una subclase debe aceptar un UUID específico."""
        eid = AId(value=SAMPLE_UUID)
        assert eid.value == SAMPLE_UUID
        assert type(eid) is AId


# ──────────────────────────────────────────────
# 2. Igualdad
# ──────────────────────────────────────────────

class TestEquality:
    def test_same_type_same_value_are_equal(self):
        """Dos EntityId del mismo tipo con el mismo UUID deben ser iguales."""
        a = EntityId(value=SAMPLE_UUID)
        b = EntityId(value=SAMPLE_UUID)
        assert a == b

    def test_same_type_different_value_not_equal(self):
        """Dos EntityId del mismo tipo con diferente UUID no deben ser iguales."""
        a = EntityId(value=SAMPLE_UUID)
        b = EntityId(value=ANOTHER_UUID)
        assert a != b

    def test_equal_ids_have_same_hash(self):
        """Dos EntityId iguales deben tener el mismo hash."""
        a = EntityId(value=SAMPLE_UUID)
        b = EntityId(value=SAMPLE_UUID)
        assert hash(a) == hash(b)

    def test_different_type_same_value_not_equal(self):
        """Dos subtipos diferentes con el mismo UUID NO deben ser iguales."""
        u = SAMPLE_UUID
        a = AId(value=u)
        b = BId(value=u)
        assert a != b

    def test_base_vs_subclass_not_equal(self):
        """EntityId base y subclase con mismo UUID NO son iguales."""
        u = SAMPLE_UUID
        base = EntityId(value=u)
        sub = AId(value=u)
        assert base != sub
        assert sub != base

    def test_equals_string_returns_false(self):
        """Comparación con string debe retornar False."""
        eid = EntityId(value=SAMPLE_UUID)
        assert (eid == "some-string") is False

    def test_equals_int_returns_false(self):
        """Comparación con int debe retornar False."""
        eid = EntityId(value=SAMPLE_UUID)
        assert (eid == 42) is False

    def test_equals_float_returns_false(self):
        """Comparación con float debe retornar False."""
        eid = EntityId(value=SAMPLE_UUID)
        assert (eid == 3.14) is False

    def test_equals_list_returns_false(self):
        """Comparación con list debe retornar False."""
        eid = EntityId(value=SAMPLE_UUID)
        assert (eid == [1, 2, 3]) is False

    def test_equals_dict_returns_false(self):
        """Comparación con dict debe retornar False."""
        eid = EntityId(value=SAMPLE_UUID)
        assert (eid == {"a": 1}) is False

    def test_equals_bool_returns_false(self):
        """Comparación con bool debe retornar False."""
        eid = EntityId(value=SAMPLE_UUID)
        assert (eid is True) is False  # evita confusión con __eq__

    def test_equals_none_returns_false(self):
        """Comparación con None debe retornar False."""
        eid = EntityId(value=SAMPLE_UUID)
        assert (eid == None) is False  # noqa: E711

    def test_not_equal_different_value(self):
        """!= debe funcionar correctamente para valores diferentes."""
        a = EntityId(value=SAMPLE_UUID)
        b = EntityId(value=ANOTHER_UUID)
        assert a != b

    def test_not_equal_different_type(self):
        """!= debe retornar True para tipos diferentes."""
        u = SAMPLE_UUID
        assert AId(value=u) != BId(value=u)

    def test_identity_is_not_equality(self):
        """Dos objetos diferentes (is) pueden ser iguales (==)."""
        a = EntityId(value=SAMPLE_UUID)
        b = EntityId(value=SAMPLE_UUID)
        assert a is not b
        assert a == b


# ──────────────────────────────────────────────
# 3. Serialización
# ──────────────────────────────────────────────

class TestSerialization:
    def test_str_returns_uuid_string(self):
        """str(eid) debe devolver el UUID como string."""
        eid = EntityId(value=SAMPLE_UUID)
        assert str(eid) == "12345678-1234-5678-1234-567812345678"

    def test_str_no_extra_wrapping(self):
        """str(eid) NO debe incluir 'EntityId()' ni 'UUID()'."""
        eid = EntityId(value=SAMPLE_UUID)
        s = str(eid)
        assert "EntityId" not in s
        assert "UUID" not in s
        assert "(" not in s

    def test_repr_includes_type_and_value(self):
        """repr(eid) debe incluir el tipo y el UUID."""
        eid = EntityId(value=SAMPLE_UUID)
        r = repr(eid)
        assert "EntityId" in r
        assert "12345678" in r

    def test_roundtrip_from_string(self):
        """EntityId.from_string(str(eid)) debe recrear el mismo ID."""
        original = EntityId(value=SAMPLE_UUID)
        restored = EntityId.from_string(str(original))
        assert original == restored
        assert type(restored) is EntityId

    def test_from_string_standard_format(self):
        """from_string debe aceptar formato UUID estándar."""
        eid = EntityId.from_string("12345678-1234-5678-1234-567812345678")
        assert eid.value == SAMPLE_UUID

    def test_from_string_with_braces(self):
        """from_string debe aceptar UUID con llaves {}."""
        eid = EntityId.from_string("{12345678-1234-5678-1234-567812345678}")
        assert eid.value == SAMPLE_UUID

    def test_from_string_without_hyphens(self):
        """from_string debe aceptar UUID de 32 caracteres sin guiones."""
        eid = EntityId.from_string("12345678123456781234567812345678")
        assert eid.value == SAMPLE_UUID

    def test_from_string_with_urn(self):
        """from_string debe aceptar UUID con prefijo urn:uuid:."""
        eid = EntityId.from_string(
            "urn:uuid:12345678-1234-5678-1234-567812345678"
        )
        assert eid.value == SAMPLE_UUID

    def test_from_string_invalid_format(self):
        """from_string con string no-UUID debe lanzar ValueError."""
        with pytest.raises(ValueError):
            EntityId.from_string("not-a-uuid")

    def test_from_string_empty_string(self):
        """from_string con string vacío debe lanzar ValueError."""
        with pytest.raises(ValueError):
            EntityId.from_string("")

    def test_from_string_too_short(self):
        """from_string con string demasiado corto debe lanzar ValueError."""
        with pytest.raises(ValueError):
            EntityId.from_string("123")

    def test_from_string_invalid_hex(self):
        """from_string con hex inválido debe lanzar ValueError."""
        with pytest.raises(ValueError):
            EntityId.from_string("gggggggg-gggg-gggg-gggg-gggggggggggg")

    def test_from_string_on_subclass_preserves_type(self):
        """from_string en subclase debe retornar instancia de la subclase."""
        eid = AId.from_string("12345678-1234-5678-1234-567812345678")
        assert type(eid) is AId
        assert eid.value == SAMPLE_UUID


# ──────────────────────────────────────────────
# 4. JSON Serialization
# ──────────────────────────────────────────────

class TestJsonSerialization:
    def test_encoder_serializes_entity_id(self):
        """FoundationEncoder debe serializar EntityId a string UUID."""
        eid = EntityId(value=SAMPLE_UUID)
        result = json.dumps(eid, cls=FoundationEncoder)
        assert result == '"12345678-1234-5678-1234-567812345678"'

    def test_encoder_in_dict(self):
        """FoundationEncoder debe serializar EntityId dentro de un dict."""
        eid = EntityId(value=SAMPLE_UUID)
        result = json.dumps({"id": eid}, cls=FoundationEncoder)
        assert result == '{"id": "12345678-1234-5678-1234-567812345678"}'

    def test_encoder_with_list(self):
        """FoundationEncoder debe serializar una lista de EntityIds."""
        eid1 = EntityId(value=SAMPLE_UUID)
        eid2 = EntityId(value=ANOTHER_UUID)
        result = json.dumps([eid1, eid2], cls=FoundationEncoder)
        assert result == (
            '["12345678-1234-5678-1234-567812345678", '
            '"87654321-4321-8765-4321-876543210987"]'
        )

    def test_encoder_with_native_types(self):
        """FoundationEncoder no debe romper serialización de tipos nativos."""
        data = {"x": 1, "y": "hello", "z": True, "w": None}
        result = json.dumps(data, cls=FoundationEncoder)
        # Python puede reordenar keys, mejor parsear y verificar
        parsed = json.loads(result)
        assert parsed["x"] == 1
        assert parsed["y"] == "hello"
        assert parsed["z"] is True
        assert parsed["w"] is None

    def test_encoder_with_nested_structure(self):
        """FoundationEncoder debe manejar estructuras anidadas."""
        eid = EntityId(value=SAMPLE_UUID)
        data = {"user": {"id": eid, "name": "test"}}
        result = json.dumps(data, cls=FoundationEncoder)
        assert "12345678-1234-5678-1234-567812345678" in result

    def test_json_without_encoder_fails(self):
        """Serializar EntityId sin FoundationEncoder debe lanzar TypeError."""
        eid = EntityId(value=SAMPLE_UUID)
        with pytest.raises(TypeError):
            json.dumps({"id": eid})

    def test_encoder_with_unknown_type_fails(self):
        """FoundationEncoder debe lanzar TypeError para tipos no soportados."""
        with pytest.raises(TypeError):
            json.dumps({"x": object()}, cls=FoundationEncoder)

    def test_encoder_with_subclass(self):
        """FoundationEncoder debe serializar subclases de EntityId."""
        eid = AId(value=SAMPLE_UUID)
        result = json.dumps(eid, cls=FoundationEncoder)
        assert result == '"12345678-1234-5678-1234-567812345678"'


# ──────────────────────────────────────────────
# 5. Colecciones
# ──────────────────────────────────────────────

class TestCollections:
    def test_can_be_used_in_set(self):
        """EntityId debe poder almacenarse en sets."""
        s = {EntityId(value=SAMPLE_UUID), EntityId(value=ANOTHER_UUID)}
        assert len(s) == 2

    def test_set_deduplicates_same_value(self):
        """Set debe deduplicar EntityIds con el mismo UUID."""
        s = {EntityId(value=SAMPLE_UUID), EntityId(value=SAMPLE_UUID)}
        assert len(s) == 1

    def test_can_be_used_as_dict_key(self):
        """EntityId debe poder usarse como clave de diccionario."""
        eid = EntityId(value=SAMPLE_UUID)
        d = {eid: "test-value"}
        assert d[eid] == "test-value"

    def test_dict_key_overwrite(self):
        """Usar el mismo EntityId como clave debe sobrescribir el valor."""
        d = {}
        d[EntityId(value=SAMPLE_UUID)] = "first"
        d[EntityId(value=SAMPLE_UUID)] = "second"
        assert len(d) == 1
        assert d[EntityId(value=SAMPLE_UUID)] == "second"

    def test_dict_with_multiple_keys(self):
        """Dict con diferentes EntityId como claves debe tener tamaño correcto."""
        d = {
            EntityId(value=SAMPLE_UUID): "a",
            EntityId(value=ANOTHER_UUID): "b",
        }
        assert len(d) == 2

    def test_different_types_in_set(self):
        """Subtipo y base en el mismo set: son diferentes aunque tengan mismo UUID."""
        u = SAMPLE_UUID
        s = {EntityId(value=u), AId(value=u)}
        assert len(s) == 2  # tipos diferentes → diferentes en set


# ──────────────────────────────────────────────
# 6. Pickle
# ──────────────────────────────────────────────

class TestPickle:
    def test_pickle_roundtrip(self):
        """Pickle roundtrip debe preservar igualdad."""
        eid = EntityId(value=SAMPLE_UUID)
        restored = pickle.loads(pickle.dumps(eid))
        assert eid == restored

    def test_pickle_preserves_type(self):
        """Pickle debe preservar el tipo exacto."""
        eid = EntityId(value=SAMPLE_UUID)
        restored = pickle.loads(pickle.dumps(eid))
        assert type(restored) is EntityId

    def test_pickle_preserves_value(self):
        """Pickle debe preservar el valor UUID."""
        eid = EntityId(value=SAMPLE_UUID)
        restored = pickle.loads(pickle.dumps(eid))
        assert restored.value == SAMPLE_UUID

    def test_pickle_subclass_preserves_type(self):
        """Pickle de subclase debe preservar el tipo exacto."""
        eid = AId(value=SAMPLE_UUID)
        restored = pickle.loads(pickle.dumps(eid))
        assert type(restored) is AId
        assert restored == eid


# ──────────────────────────────────────────────
# 7. Copy
# ──────────────────────────────────────────────

class TestCopy:
    def test_shallow_copy_preserves_equality(self):
        """copy.copy debe preservar igualdad."""
        eid = EntityId(value=SAMPLE_UUID)
        copied = copy.copy(eid)
        assert eid == copied

    def test_deep_copy_preserves_equality(self):
        """copy.deepcopy debe preservar igualdad."""
        eid = EntityId(value=SAMPLE_UUID)
        copied = copy.deepcopy(eid)
        assert eid == copied

    def test_deep_copy_preserves_value(self):
        """copy.deepcopy debe preservar el valor UUID."""
        eid = EntityId(value=SAMPLE_UUID)
        copied = copy.deepcopy(eid)
        assert copied.value == SAMPLE_UUID

    def test_shallow_copy_of_subclass(self):
        """copy.copy debe funcionar con subclases."""
        eid = AId(value=SAMPLE_UUID)
        copied = copy.copy(eid)
        assert type(copied) is AId
        assert eid == copied


# ──────────────────────────────────────────────
# 8. Inmutabilidad
# ──────────────────────────────────────────────

class TestImmutability:
    def test_frozen_cannot_modify_value(self):
        """Modificar value debe lanzar FrozenInstanceError."""
        eid = EntityId(value=SAMPLE_UUID)
        with pytest.raises(FrozenInstanceError):
            eid.value = ANOTHER_UUID

    def test_frozen_cannot_delete_value(self):
        """Eliminar value debe lanzar FrozenInstanceError."""
        eid = EntityId(value=SAMPLE_UUID)
        with pytest.raises(FrozenInstanceError):
            del eid.value

    def test_frozen_cannot_set_new_attr(self):
        """Agregar un nuevo atributo debe lanzar FrozenInstanceError."""
        eid = EntityId(value=SAMPLE_UUID)
        with pytest.raises(FrozenInstanceError):
            eid.new_attr = "should-not-work"
