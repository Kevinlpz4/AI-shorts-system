"""
Tests para ValueObject (marker class).

Cubre:
  - Marker class: instanciación directa, subclass, isinstance
  - Igualdad estructural (sobre subclase @dataclass(frozen=True))
  - Inmutabilidad (FrozenInstanceError)
  - Validación en __post_init__
  - Serialización básica (repr, str)
  - Edge cases: comparación con no-VO, tipos diferentes
"""

from dataclasses import dataclass, FrozenInstanceError

import pytest

from foundation import ValueObject


# ══════════════════════════════════════════════
# Helpers concretos para testing
# ══════════════════════════════════════════════

@dataclass(frozen=True)
class Address(ValueObject):
    """Value Object concreto con @dataclass(frozen=True)."""
    street: str
    city: str


@dataclass(frozen=True)
class PositiveInt(ValueObject):
    """Value Object concreto con validación en __post_init__."""
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("value must be positive")


@dataclass(frozen=True)
class PersonName(ValueObject):
    """Otro VO para testear comparación entre tipos diferentes."""
    first: str
    last: str


class ManualVO(ValueObject):
    """VO sin @dataclass — válido pero responsibility del desarrollador."""
    def __init__(self, value: str) -> None:
        self._value = value

    @property
    def value(self) -> str:
        return self._value


# ══════════════════════════════════════════════
# 1. Marker class
# ══════════════════════════════════════════════

class TestMarkerClass:
    def test_can_instantiate_directly(self):
        """ValueObject() debe poder instanciarse directamente."""
        vo = ValueObject()
        assert isinstance(vo, ValueObject)

    def test_can_subclass_with_dataclass(self):
        """Subclase con @dataclass(frozen=True) debe funcionar."""
        addr = Address(street="Main", city="NYC")
        assert isinstance(addr, Address)
        assert isinstance(addr, ValueObject)

    def test_can_subclass_without_dataclass(self):
        """Subclase sin @dataclass también debe funcionar."""
        vo = ManualVO("test")
        assert isinstance(vo, ManualVO)
        assert isinstance(vo, ValueObject)

    def test_isinstance_check_polymorphic(self):
        """isinstance debe funcionar polimórficamente."""
        addr = Address(street="Main", city="NYC")
        assert isinstance(addr, ValueObject)

    def test_vo_without_fields_is_instance(self):
        """ValueObject sin atributos debe ser instanciable."""
        class EmptyVO(ValueObject):
            pass
        vo = EmptyVO()
        assert isinstance(vo, ValueObject)

    def test_direct_value_object_has_no_auto_equality(self):
        """ValueObject directo NO tiene __eq__ automático (es marker class)."""
        a = ValueObject()
        b = ValueObject()
        # Sin @dataclass, dos instancias de marker class son diferentes objetos
        assert a is not b


# ══════════════════════════════════════════════
# 2. Igualdad estructural (sobre subclase @dataclass)
# ══════════════════════════════════════════════

class TestStructuralEquality:
    def test_same_values_are_equal(self):
        """Mismos valores deben ser iguales."""
        a = Address(street="Main", city="NYC")
        b = Address(street="Main", city="NYC")
        assert a == b

    def test_different_values_not_equal(self):
        """Valores diferentes no deben ser iguales."""
        a = Address(street="Main", city="NYC")
        b = Address(street="Other", city="NYC")
        assert a != b

    def test_equal_vos_have_same_hash(self):
        """VOs iguales deben tener el mismo hash."""
        a = Address(street="Main", city="NYC")
        b = Address(street="Main", city="NYC")
        assert hash(a) == hash(b)

    def test_compare_with_non_vo_returns_false(self):
        """Comparar VO con tipo no-VO debe devolver False."""
        addr = Address(street="Main", city="NYC")
        assert (addr == "string") is False
        assert (addr == 42) is False
        assert (addr is not None)

    def test_vos_with_different_types_not_equal(self):
        """VOs de diferentes tipos no deben ser iguales aunque tengan mismos valores."""
        addr = Address(street="Main", city="NYC")
        name = PersonName(first="Main", last="NYC")
        assert addr != name

    def test_symmetric_equality(self):
        """Igualdad debe ser simétrica."""
        a = Address(street="Main", city="NYC")
        b = Address(street="Main", city="NYC")
        assert a == b
        assert b == a

    def test_reflexive_equality(self):
        """Un VO debe ser igual a sí mismo."""
        a = Address(street="Main", city="NYC")
        assert a == a


# ══════════════════════════════════════════════
# 3. Inmutabilidad (sobre subclase @dataclass(frozen=True))
# ══════════════════════════════════════════════

class TestImmutability:
    def test_cannot_modify_field(self):
        """Reasignar un field debe lanzar FrozenInstanceError."""
        addr = Address(street="Main", city="NYC")
        with pytest.raises(FrozenInstanceError):
            addr.street = "Other"  # type: ignore[misc]

    def test_cannot_add_new_field(self):
        """Agregar un nuevo atributo debe lanzar FrozenInstanceError."""
        addr = Address(street="Main", city="NYC")
        with pytest.raises(FrozenInstanceError):
            addr.new_attr = "value"  # type: ignore[attr-defined]


# ══════════════════════════════════════════════
# 4. Validación en __post_init__
# ══════════════════════════════════════════════

class TestPostInitValidation:
    def test_post_init_validates_valid_input(self):
        """Valor válido debe crear la instancia."""
        vo = PositiveInt(value=5)
        assert vo.value == 5

    def test_post_init_rejects_invalid_input(self):
        """Valor inválido debe lanzar ValueError."""
        with pytest.raises(ValueError, match="value must be positive"):
            PositiveInt(value=-1)

    def test_post_init_rejects_zero(self):
        """Cero también debe ser rechazado si la validación dice positive."""
        with pytest.raises(ValueError, match="value must be positive"):
            PositiveInt(value=0)


# ══════════════════════════════════════════════
# 5. Serialización básica
# ══════════════════════════════════════════════

class TestSerialization:
    def test_repr_includes_fields(self):
        """repr debe incluir los campos del VO."""
        addr = Address(street="Main", city="NYC")
        assert "street='Main'" in repr(addr)
        assert "city='NYC'" in repr(addr)

    def test_repr_includes_class_name(self):
        """repr debe incluir el nombre de la clase."""
        addr = Address(street="Main", city="NYC")
        assert repr(addr).startswith("Address(")
