"""
Clock Port — Abstracción del tiempo para testabilidad y desacoplamiento.

Arquitectura (port & adapter pattern):
    ClockPort (Protocol)
    ├── SystemClock     — producción: datetime.now(timezone.utc)
    └── FrozenClock     — tests: datetime congelado + advance()

Principios:
    - Siempre retorna datetime timezone-aware (UTC).
    - Zero dependencias externas (stdlib-only).
    - ClockPort es un Protocol estructural — NO requiere herencia explícita.
    - FrozenClock.advance() permite simular paso del tiempo sin crear
      nuevas instancias, mejorando ergonomía y determinismo en tests.

Uso::

    # Producción
    clock = SystemClock()
    now = clock.now()  # datetime.now(timezone.utc)

    # Tests
    clock = FrozenClock(datetime(2026, 6, 1, tzinfo=timezone.utc))
    clock.advance(timedelta(hours=2))
    assert clock.now() == datetime(2026, 6, 1, 2, 0, tzinfo=timezone.utc)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Protocol


class ClockPort(Protocol):
    """
    Puerto: provee el tiempo actual.

    Responsabilidades:
        - Devolver datetime actual en UTC (timezone-aware).
        - Proveer una fuente única de tiempo para toda una operación.

    NO hace:
        - No formatea fechas.
        - No convierte timezones.
        - No sabe de dominio.

    Es un Protocol estructural: cualquier objeto con ``now()`` que
    retorne ``datetime`` cumple el contrato. No requiere herencia.

    Uso en BCs::

        class MyEntity:
            def __init__(self, clock: ClockPort | None = None):
                self._clock = clock or SystemClock()

            def is_expired(self) -> bool:
                return self._expires_at < self._clock.now()
    """

    def now(self) -> datetime:
        """
        Devuelve el datetime actual en UTC (timezone-aware).

        Returns:
            datetime con timezone.utc.

        Garantiza:
            - Siempre timezone-aware (NUNCA naive).
            - Siempre UTC.
        """


class SystemClock:
    """
    Clock real de producción.

    Usa ``datetime.now(timezone.utc)`` para obtener el tiempo actual.

    Comportamiento:
        - Cada llamada a ``now()`` refleja el tiempo real.
        - ``utc_today()`` deriva de ``now()``.

    Uso::

        clock = SystemClock()
        now = clock.now()       # ej: 2026-07-02 22:30:00+00:00
        today = clock.utc_today()  # ej: 2026-07-02
    """

    def now(self) -> datetime:
        """Devuelve el datetime actual UTC (timezone-aware)."""
        return datetime.now(timezone.utc)

    def utc_today(self) -> date:
        """Devuelve la fecha UTC actual."""
        return self.now().date()


class FrozenClock:
    """
    Clock congelado para tests determinísticos.

    Siempre devuelve el mismo ``datetime`` a menos que se avance
    explícitamente con ``advance()``.

    Atributos:
        _frozen: El datetime congelado actual.

    Uso::

        clock = FrozenClock(datetime(2026, 6, 1, tzinfo=timezone.utc))
        assert clock.now() == datetime(2026, 6, 1, tzinfo=timezone.utc)

        clock.advance(timedelta(days=5))
        assert clock.now() == datetime(2026, 6, 6, tzinfo=timezone.utc)
    """

    _DEFAULT_FROZEN: datetime = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __init__(self, now: datetime | None = None) -> None:
        """
        Inicializa el clock con un datetime congelado.

        Args:
            now: Datetime congelado inicial. Si es ``None``, usa
                 ``2026-01-01T00:00:00+00:00`` como default.

        Raises:
            ValueError: Si ``now`` es naive (sin timezone).
        """
        if now is None:
            now = self._DEFAULT_FROZEN
        if now.tzinfo is None:
            raise ValueError("FrozenClock requires timezone-aware datetime, got naive")
        self._frozen = now

    def now(self) -> datetime:
        """
        Devuelve el datetime congelado actual.

        Siempre retorna el mismo valor a menos que se llame a
        ``advance()`` o se cree una nueva instancia.
        """
        return self._frozen

    def utc_today(self) -> date:
        """Devuelve la fecha del datetime congelado."""
        return self._frozen.date()

    def advance(self, delta: timedelta) -> None:
        """
        Adelanta (o retrocede) el tiempo congelado.

     Útil para simular paso del tiempo en tests sin crear
        múltiples instancias de FrozenClock.

        Args:
            delta: Cantidad de tiempo a avanzar. Usar valores
                   positivos para avanzar, negativos para retroceder.

        Uso::

            clock = FrozenClock()
            clock.advance(timedelta(hours=3))
            clock.advance(timedelta(days=-1))  # retroceder
        """
        self._frozen += delta

    def __eq__(self, other: object) -> bool:
        """Dos FrozenClock son iguales si su tiempo congelado es el mismo."""
        if not isinstance(other, FrozenClock):
            return NotImplemented
        return self._frozen == other._frozen

    def __hash__(self) -> int:
        """Hash basado en el tiempo congelado."""
        return hash(self._frozen)

    def __repr__(self) -> str:
        return f"FrozenClock({self._frozen.isoformat()})"
