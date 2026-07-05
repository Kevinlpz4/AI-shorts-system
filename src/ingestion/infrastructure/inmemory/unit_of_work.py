"""
InMemoryUnitOfWork — context manager transaccional en memoria.

Simula commit/rollback para testing y desarrollo. Los cambios en repositorios
in-memory son inmediatos (porque no hay una transacción real), pero la UoW
registra si commit() o rollback() fueron llamados, permitiendo verificar el
ciclo transaccional en tests.

Uso::

    with uow:
        repo.save(entity)
        uow.commit()   # marca committed = True
    # Si ocurre una excepción dentro del with, __exit__ llama rollback()
"""

from __future__ import annotations

from ingestion.application.ports.unit_of_work import UnitOfWork


class InMemoryUnitOfWork:
    """UnitOfWork en memoria con context manager.

    Attributes:
        is_committed: ``True`` después de llamar a commit().
        is_rolled_back: ``True`` después de llamar a rollback() o si
            ocurre una excepción en el context manager.
    """

    def __init__(self) -> None:
        self._committed = False
        self._rolled_back = False

    @property
    def is_committed(self) -> bool:
        """``True`` si commit() fue llamado."""
        return self._committed

    @property
    def is_rolled_back(self) -> bool:
        """``True`` si rollback() fue llamado (o excepción en __exit__)."""
        return self._rolled_back

    def __enter__(self) -> InMemoryUnitOfWork:
        """Inicia una transacción."""
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_val: object,
        exc_tb: object,
    ) -> None:
        """Finaliza la transacción.

        Si exc_type no es None (hubo excepción), hace rollback automático.
        """
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        """Persiste los cambios acumulados (marca committed)."""
        self._committed = True

    def rollback(self) -> None:
        """Descarta los cambios acumulados (marca rolled_back)."""
        self._rolled_back = True
