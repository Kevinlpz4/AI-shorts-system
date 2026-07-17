"""
ClockPort — Abstracción del reloj del sistema.

Define el contrato para obtener la hora actual. Permite inyectar
un reloj falso en tests y un reloj real en producción.

Uso::

    class RealClock:
        def now(self) -> datetime:
            return datetime.now(timezone.utc)

    clock = RealClock()
    timestamp = clock.now()
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Port para obtener la hora actual del sistema.

    Responsabilidades:
        - now(): Retornar la hora actual.

    NO hace:
        - No calcula duraciones.
        - No compara fechas.
        - No formatea timestamps.

    Uso típico:
        Inyectar un ``FakeClock`` en tests para controlar el tiempo.
    """

    def now(self) -> datetime:
        """Retorna la hora actual.

        Returns:
            datetime con la hora actual.
        """
        ...
