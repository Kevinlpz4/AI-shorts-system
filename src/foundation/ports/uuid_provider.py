"""
UUID Provider — Abstracción de generación de UUIDs para testabilidad.

Arquitectura (port & adapter pattern):
    UUIDProvider (Protocol)
    ├── SystemUUIDProvider         — producción: uuid4() (aleatorio)
    └── SequentialUUIDProvider     — tests: contador secuencial (determinístico)

Principios:
    - Zero dependencias externas (stdlib-only).
    - UUIDProvider es un Protocol estructural — NO requiere herencia explícita.
    - SequentialUUIDProvider ES exclusivamente para testing. Su propósito es
      determinismo y reproducibilidad, NO seguridad.

Uso::

    # Producción
    provider = SystemUUIDProvider()
    uid = provider.new()  # uuid4()

    # Tests
    provider = SequentialUUIDProvider(start=1)
    uid1 = provider.new()  # UUID(int=1)
    uid2 = provider.new()  # UUID(int=2)
    # Misma secuencia siempre para el mismo start
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID, uuid4


class UUIDProvider(Protocol):
    """
    Puerto: genera UUIDs.

    Responsabilidades:
        - Generar UUIDs únicos.
        - (Opcional) Generar UUIDs determinísticos para tests.

    NO hace:
        - No valida UUIDs (eso es responsabilidad de EntityId).
        - No formatea UUIDs.

    Es un Protocol estructural: cualquier objeto con ``new()`` que
    retorne ``UUID`` cumple el contrato.

    Uso en BCs::

        class MyEntity:
            def __init__(self, uuid_provider: UUIDProvider | None = None):
                self._uuid_provider = uuid_provider or SystemUUIDProvider()

            @classmethod
            def create(cls, ...) -> MyEntity:
                return cls(id=EntityId(self._uuid_provider.new()), ...)
    """

    def new(self) -> UUID:
        """
        Genera un nuevo UUID.

        Returns:
            Un UUID único (o determinístico, según la implementación).
        """


class SystemUUIDProvider:
    """
    Proveedor real de UUIDs para producción.

    Usa ``uuid4()`` para generar UUIDs aleatorios.
    Cada llamada produce un UUID diferente y no predecible.

    Uso::

        provider = SystemUUIDProvider()
        uid = provider.new()  # uuid4() — aleatorio, único
    """

    def new(self) -> UUID:
        """Genera un UUID aleatorio vía ``uuid4()``."""
        return uuid4()


class SequentialUUIDProvider:
    """
    Proveedor secuencial de UUIDs para tests determinísticos.

    Genera UUIDs con valor entero incremental, produciendo SIEMPRE
    la misma secuencia para el mismo ``start``.

    **¿Por qué existe?**

    El objetivo NO es seguridad. Es **determinismo y reproducibilidad
    en tests**. Con ``SequentialUUIDProvider``:

    - Los IDs son predecibles: la primera llamada siempre retorna
      el mismo UUID para un mismo ``start``.
    - Se pueden escribir assertions sobre IDs en tests.
    - No se depende de ``uuid4()`` (aleatorio) ni de ``uuid5()``
      (que requiere namespace fijo y puede dar falsa sensación
      de "estándar" cuando en realidad es arbitrario).

    **¿Por qué no uuid5()?**

    Aunque ``uuid5()`` produce UUIDs determinísticos, requiere un
    namespace fijo y un nombre. Para un secuenciador simple basado
    en contador, usar ``uuid5(NAMESPACE, str(counter))`` introduce
    una dependencia de un namespace arbitrario sin beneficio real.
    Usar directamente el valor entero del contador como ``UUID(int=...)``
    es más simple, más rápido, y produce UUIDs igualmente válidos.

    Uso::

        provider = SequentialUUIDProvider(start=1)
        uid1 = provider.new()  # UUID(int=1) → 00000000-0000-0000-0000-000000000001
        uid2 = provider.new()  # UUID(int=2) → 00000000-0000-0000-0000-000000000002

        provider2 = SequentialUUIDProvider(start=100)
        uid3 = provider2.new()  # UUID(int=100)

    Args:
        start: Valor inicial del contador (default: 1).
               La primera llamada a ``new()`` produce ``UUID(int=start)``.
    """

    def __init__(self, start: int = 1) -> None:
        """
        Inicializa el proveedor con un valor inicial del contador.

        Args:
            start: Valor para el primer UUID (default: 1).
                   Debe ser un entero no negativo. Valores negativos
                   producen UUIDs válidos pero pueden causar confusión.
        """
        self._counter = start

    def new(self) -> UUID:
        """
        Genera el siguiente UUID secuencial.

        Returns:
            UUID con valor entero incremental.
            La primera llamada retorna ``UUID(int=start)``.
        """
        result = UUID(int=self._counter)
        self._counter += 1
        return result
