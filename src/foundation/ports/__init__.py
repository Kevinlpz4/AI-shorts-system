"""
Foundation Ports — Abstracciones de infraestructura.

Exporta los puertos de infraestructura compartidos por todos
los Bounded Contexts para garantizar testabilidad y desacoplamiento.

Componentes:
    ClockPort (Protocol)       — Abstracción del tiempo
    SystemClock                — Clock real (datetime.now(timezone.utc))
    FrozenClock                — Clock congelado para tests (con advance())
    UUIDProvider (Protocol)    — Abstracción de generación de UUIDs
    SystemUUIDProvider         — UUID real (uuid4())
    SequentialUUIDProvider     — UUID secuencial determinístico para tests

Uso::

    from foundation.ports import ClockPort, SystemClock, FrozenClock
    from foundation.ports import UUIDProvider, SystemUUIDProvider, SequentialUUIDProvider
"""

from foundation.ports.clock import ClockPort, FrozenClock, SystemClock
from foundation.ports.uuid_provider import (
    SequentialUUIDProvider,
    SystemUUIDProvider,
    UUIDProvider,
)

__all__ = [
    "ClockPort",
    "FrozenClock",
    "SequentialUUIDProvider",
    "SystemClock",
    "SystemUUIDProvider",
    "UUIDProvider",
]
