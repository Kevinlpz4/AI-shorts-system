"""
UnitOfWork Port — Abstracción de transacciones.

Define el contrato para manejo de transacciones en la capa de aplicación.
Cualquier implementación (SQLAlchemy, mock, etc.) que cumpla este Protocol
puede ser inyectada en los Services.

Uso::

    with self._uow:
        # operaciones dentro de la transacción
        self._uow.commit()

    Si commit() no se llama explícitamente, o si ocurre una excepción,
    el context manager debe hacer rollback automático en __exit__.
"""

from __future__ import annotations

from typing import Protocol


class UnitOfWork(Protocol):
    """Context manager transaccional.

    Responsabilidades:
        - Proveer un context manager para delimitar transacciones.
        - commit(): Persistir los cambios acumulados.
        - rollback(): Descartar los cambios acumulados.
        - __exit__: Hacer rollback automático si hubo excepción.

    NO hace:
        - No sabe de repositorios ni entidades.
        - No emite eventos.
        - No maneja concurrencia (optimistic locking es responsabilidad
          de la implementación concreta).
    """

    def __enter__(self) -> UnitOfWork:
        """Inicia una transacción."""
        ...

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Finaliza la transacción.

        Si exc_type no es None (hubo excepción), hace rollback automático.
        """
        ...

    def commit(self) -> None:
        """Persiste los cambios acumulados en la transacción actual."""
        ...

    def rollback(self) -> None:
        """Descarta los cambios acumulados en la transacción actual."""
        ...
