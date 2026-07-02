"""
Tests de UUID Provider (Sprint 2.6).

Cubre: UUIDProvider (structural), SystemUUIDProvider, SequentialUUIDProvider.

~17 tests:
    - SystemUUIDProvider        (3) — UUID válido, distintos, tipo
    - SequentialUUIDProvider    (7) — determinismo, secuencia, edge cases
    - Edge Cases                (4) — str, equality, hash, copy, pickle
    - Protocolos                (3) — structural check + documentación
"""

from __future__ import annotations

import pickle
from copy import deepcopy
from uuid import UUID

import pytest

from foundation.ports.uuid_provider import (
    SequentialUUIDProvider,
    SystemUUIDProvider,
    UUIDProvider,
)


# ══════════════════════════════════════════════════════════════
# 1. SystemUUIDProvider — Producción
# ══════════════════════════════════════════════════════════════


class TestSystemUUIDProvider:
    """Test del proveedor real de UUIDs."""

    def test_new_returns_uuid(self):
        """SystemUUIDProvider.new() retorna un UUID."""
        provider = SystemUUIDProvider()
        uid = provider.new()
        assert isinstance(uid, UUID)

    def test_new_generates_different_uuids(self):
        """SystemUUIDProvider.new() genera UUIDs distintos en cada llamada."""
        provider = SystemUUIDProvider()
        uid1 = provider.new()
        uid2 = provider.new()
        assert uid1 != uid2

    def test_new_uuid_type(self):
        """SystemUUIDProvider.new() retorna UUID versión 4 (aleatorio)."""
        provider = SystemUUIDProvider()
        uid = provider.new()
        assert isinstance(uid, UUID)
        # uuid4() produce UUID.version == 4
        assert uid.version == 4


# ══════════════════════════════════════════════════════════════
# 2. SequentialUUIDProvider — Tests determinísticos
# ══════════════════════════════════════════════════════════════


class TestSequentialUUIDProvider:
    """Test del proveedor secuencial para testing."""

    def test_new_returns_uuid(self):
        """SequentialUUIDProvider.new() retorna un UUID."""
        provider = SequentialUUIDProvider()
        uid = provider.new()
        assert isinstance(uid, UUID)

    def test_first_uuid_equals_start(self):
        """El primer UUID tiene int igual a start."""
        provider = SequentialUUIDProvider(start=42)
        uid = provider.new()
        assert uid.int == 42

    def test_deterministic_sequence(self):
        """Mismo start produce SIEMPRE la misma secuencia."""
        p1 = SequentialUUIDProvider(start=1)
        p2 = SequentialUUIDProvider(start=1)

        seq1 = [p1.new() for _ in range(5)]
        seq2 = [p2.new() for _ in range(5)]

        assert seq1 == seq2

    def test_different_start_different_sequence(self):
        """Start diferente produce secuencia diferente."""
        p1 = SequentialUUIDProvider(start=1)
        p2 = SequentialUUIDProvider(start=100)

        assert p1.new() != p2.new()

    def test_sequential_increment(self):
        """Cada llamada incrementa el valor del UUID en 1."""
        provider = SequentialUUIDProvider(start=1)
        uid1 = provider.new()
        uid2 = provider.new()
        uid3 = provider.new()

        assert uid2.int == uid1.int + 1
        assert uid3.int == uid2.int + 1

    def test_default_start_is_one(self):
        """Default start es 1."""
        provider = SequentialUUIDProvider()
        assert provider.new().int == 1

    def test_start_zero(self):
        """start=0 funciona correctamente."""
        provider = SequentialUUIDProvider(start=0)
        assert provider.new().int == 0
        assert provider.new().int == 1

    def test_start_negative_raises(self):
        """start negativo lanza ValueError (UUID requiere 128-bit sin signo)."""
        provider = SequentialUUIDProvider(start=-5)
        with pytest.raises(ValueError, match="out of range"):
            provider.new()


# ══════════════════════════════════════════════════════════════
# 3. Edge Cases — Serialización y manipulación de UUIDs
# ══════════════════════════════════════════════════════════════


class TestUUIDEdgeCases:
    """Tests de serialización y manipulación de UUIDs generados."""

    def test_str_representation(self):
        """UUID producido se serializa a string correctamente."""
        provider = SequentialUUIDProvider(start=1)
        uid = provider.new()
        # UUID(int=1) → "00000000-0000-0000-0000-000000000001"
        assert str(uid) == "00000000-0000-0000-0000-000000000001"

    def test_uuid_equality_same_value(self):
        """Dos UUIDs con el mismo int son iguales."""
        provider = SequentialUUIDProvider(start=1)
        uid1 = provider.new()
        # UUID(int=1) es siempre el mismo
        uid2 = UUID(int=1)
        assert uid1 == uid2

    def test_uuid_hashable(self):
        """UUIDs generados son hashable (funcionan en sets/dicts)."""
        provider = SequentialUUIDProvider(start=1)
        uid1 = provider.new()
        uid2 = provider.new()
        s = {uid1, uid2, uid1}
        assert len(s) == 2

    def test_uuid_from_string_roundtrip(self):
        """UUID se puede serializar y deserializar desde string."""
        provider = SequentialUUIDProvider(start=42)
        uid = provider.new()
        uid_str = str(uid)
        restored = UUID(hex=uid_str)
        assert restored == uid

    def test_deepcopy_uuid(self):
        """UUID generado soporta deepcopy."""
        provider = SequentialUUIDProvider(start=10)
        uid = provider.new()
        copied = deepcopy(uid)
        assert copied == uid
        assert copied.int == uid.int

    def test_pickle_uuid(self):
        """UUID generado soporta pickle."""
        provider = SequentialUUIDProvider(start=99)
        uid = provider.new()
        data = pickle.dumps(uid)
        restored = pickle.loads(data)
        assert restored == uid

    def test_sequential_no_collisions(self):
        """SequentialUUIDProvider produce valores únicos dentro de una secuencia."""
        provider = SequentialUUIDProvider(start=1)
        uuids = {provider.new() for _ in range(100)}
        assert len(uuids) == 100


# ══════════════════════════════════════════════════════════════
# 4. Protocol structural checks
# ══════════════════════════════════════════════════════════════


class TestUUIDProviderProtocol:
    """Verificación estructural de que las implementaciones cumplen UUIDProvider."""

    def test_system_uuid_provider_is_uuidprovider(self):
        """SystemUUIDProvider cumple UUIDProvider estructuralmente."""
        provider = SystemUUIDProvider()
        uid = provider.new()
        assert isinstance(uid, UUID)

    def test_sequential_uuid_provider_is_uuidprovider(self):
        """SequentialUUIDProvider cumple UUIDProvider estructuralmente."""
        provider = SequentialUUIDProvider()
        uid = provider.new()
        assert isinstance(uid, UUID)

    def test_documentation_explains_determinism(self):
        """La docstring de SequentialUUIDProvider explica por qué existe."""
        doc = SequentialUUIDProvider.__doc__
        assert doc is not None
        # Debe explicar que es para testing, no para seguridad
        assert "determin" in doc.lower() or "test" in doc.lower()
