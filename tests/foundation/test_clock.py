"""
Tests de Clock Port (Sprint 2.6).

Cubre: ClockPort (structural), SystemClock, FrozenClock.

~20 tests:
    - SystemClock     (5) — timezone, UTC, utc_today, variación
    - FrozenClock     (10) — default, custom, advance, equality, hash, repr
    - Protocolos      (2) — structural check
    - Edge Cases      (3) — naive rejection, copy, pickle
"""

from __future__ import annotations

import pickle
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone

import pytest

from foundation.ports.clock import ClockPort, FrozenClock, SystemClock


# ══════════════════════════════════════════════════════════════
# 1. SystemClock — Producción
# ══════════════════════════════════════════════════════════════


class TestSystemClock:
    """Test del Clock real de producción."""

    def test_now_is_timezone_aware(self):
        """SystemClock.now() siempre retorna datetime timezone-aware."""
        clock = SystemClock()
        now = clock.now()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc

    def test_now_is_utc(self):
        """SystemClock.now() retorna UTC (offset 0)."""
        clock = SystemClock()
        now = clock.now()
        assert now.utcoffset() == timedelta(0)

    def test_utc_today_returns_date(self):
        """SystemClock.utc_today() retorna un date."""
        clock = SystemClock()
        today = clock.utc_today()
        assert isinstance(today, date)

    def test_utc_today_matches_now(self):
        """SystemClock.utc_today() deriva de now()."""
        clock = SystemClock()
        today = clock.utc_today()
        now = clock.now()
        assert today == now.date()

    def test_now_varies_over_time(self):
        """SystemClock.now() retorna valores diferentes (el tiempo pasa)."""
        clock = SystemClock()
        t1 = clock.now()
        t2 = clock.now()
        # Es posible que sean iguales si el test corre en <1μs,
        # pero en la práctica casi siempre difieren.
        # Lo importante es que t2 NO sea anterior a t1.
        assert t2 >= t1


# ══════════════════════════════════════════════════════════════
# 2. FrozenClock — Tests determinísticos
# ══════════════════════════════════════════════════════════════


class TestFrozenClock:
    """Test del Clock congelado para testing."""

    def test_default_constructor(self):
        """FrozenClock() usa default 2026-01-01T00:00:00+00:00."""
        clock = FrozenClock()
        expected = datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert clock.now() == expected

    def test_custom_datetime(self):
        """FrozenClock(now=...) usa el datetime provisto."""
        dt = datetime(2026, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        clock = FrozenClock(now=dt)
        assert clock.now() == dt

    def test_frozen_does_not_change(self):
        """FrozenClock.now() siempre retorna el mismo valor."""
        dt = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
        clock = FrozenClock(now=dt)
        assert clock.now() == dt
        assert clock.now() == dt
        assert clock.now() == dt  # siempre igual

    def test_advance_moves_forward(self):
        """FrozenClock.advance() adelanta el tiempo."""
        clock = FrozenClock()
        clock.advance(timedelta(hours=5))
        expected = datetime(2026, 1, 1, 5, 0, tzinfo=timezone.utc)
        assert clock.now() == expected

    def test_advance_multiple_times(self):
        """Múltiples advance() acumulan."""
        clock = FrozenClock()
        clock.advance(timedelta(days=1))
        clock.advance(timedelta(hours=6))
        clock.advance(timedelta(minutes=30))
        expected = datetime(2026, 1, 2, 6, 30, tzinfo=timezone.utc)
        assert clock.now() == expected

    def test_advance_negative(self):
        """FrozenClock.advance() con delta negativo retrocede."""
        clock = FrozenClock()
        clock.advance(timedelta(days=-5))
        expected = datetime(2025, 12, 27, tzinfo=timezone.utc)
        assert clock.now() == expected

    def test_utc_today(self):
        """FrozenClock.utc_today() retorna fecha del frozen datetime."""
        dt = datetime(2026, 12, 25, 18, 30, tzinfo=timezone.utc)
        clock = FrozenClock(now=dt)
        assert clock.utc_today() == date(2026, 12, 25)

    def test_equality_same_time(self):
        """Dos FrozenClock con mismo tiempo son iguales."""
        dt = datetime(2026, 3, 15, tzinfo=timezone.utc)
        c1 = FrozenClock(now=dt)
        c2 = FrozenClock(now=dt)
        assert c1 == c2

    def test_inequality_different_time(self):
        """Dos FrozenClock con diferente tiempo NO son iguales."""
        c1 = FrozenClock()
        c2 = FrozenClock(now=datetime(2026, 6, 1, tzinfo=timezone.utc))
        assert c1 != c2

    def test_hash(self):
        """FrozenClock tiene hash consistente con equality."""
        dt = datetime(2026, 3, 15, tzinfo=timezone.utc)
        c1 = FrozenClock(now=dt)
        c2 = FrozenClock(now=dt)
        assert hash(c1) == hash(c2)

    def test_repr(self):
        """FrozenClock.__repr__ incluye el datetime."""
        dt = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        clock = FrozenClock(now=dt)
        assert "FrozenClock" in repr(clock)
        assert "2026-06-01T12:00:00+00:00" in repr(clock)

    def test_deepcopy(self):
        """FrozenClock soporta deepcopy."""
        dt = datetime(2026, 3, 15, tzinfo=timezone.utc)
        clock = FrozenClock(now=dt)
        clock.advance(timedelta(hours=2))
        copied = deepcopy(clock)
        assert copied == clock
        # Avanzar el original no afecta la copia
        clock.advance(timedelta(hours=1))
        assert copied.now() != clock.now()

    def test_pickle_roundtrip(self):
        """FrozenClock soporta pickle y preserva estado."""
        dt = datetime(2026, 7, 4, 18, 30, tzinfo=timezone.utc)
        clock = FrozenClock(now=dt)
        clock.advance(timedelta(minutes=15))
        data = pickle.dumps(clock)
        restored = pickle.loads(data)
        assert restored == clock
        assert restored.now() == clock.now()

    def test_rejects_naive_datetime(self):
        """FrozenClock rechaza datetime naive (sin timezone)."""
        with pytest.raises(ValueError, match="timezone"):
            FrozenClock(now=datetime(2026, 1, 1))

    def test_not_equal_to_non_frozenclock(self):
        """FrozenClock no es igual a otros tipos."""
        clock = FrozenClock()
        assert clock != "not a clock"
        assert clock != 42
        assert clock != SystemClock()


# ══════════════════════════════════════════════════════════════
# 3. Protocol structural checks
# ══════════════════════════════════════════════════════════════


class TestClockPortProtocol:
    """Verificación estructural de que las implementaciones cumplen ClockPort."""

    def test_systemclock_is_clockport(self):
        """SystemClock cumple ClockPort estructuralmente."""
        clock = SystemClock()
        # Duck typing: ClockPort requiere now() -> datetime
        now = clock.now()
        assert isinstance(now, datetime)

    def test_frozenclock_is_clockport(self):
        """FrozenClock cumple ClockPort estructuralmente."""
        clock = FrozenClock()
        now = clock.now()
        assert isinstance(now, datetime)
