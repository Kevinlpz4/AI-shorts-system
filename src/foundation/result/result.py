"""
Result Pattern — encapsula éxito o fracaso de una operación.

Este módulo define el tipo suma ``Result[T]`` con sus variantes
``Success[T]`` y ``Failure[T]``, junto con ``Error`` y ``ErrorCode``
para representar errores de operación de forma estructurada.

Uso:

    >>> from foundation.result import Error, ErrorCode, Result
    >>>
    >>> def divide(a: int, b: int) -> Result[float]:
    ...     if b == 0:
    ...         return Result.failure(
    ...             Error(code=ErrorCode.UNKNOWN, message="Division by zero"),
    ...         )
    ...     return Result.success(a / b)
    >>>
    >>> match divide(10, 2):
    ...     case Success(value=v):
    ...         print(v)  # 5.0
    ...     case Failure(error=e):
    ...         print(e)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

T = TypeVar("T")


class ErrorCode(str, Enum):
    """Códigos de error estandarizados.

    Foundation provee ``UNKNOWN`` como valor default.
    Cada Bounded Context define su propio ``str, Enum`` independiente::

        class IngestionErrorCode(str, Enum):
            SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"

    NOTA: ``ErrorCode`` NO es extensible por herencia. Python 3.11+ prohíbe
    subclasear Enums que tienen miembros definidos. Ver ADR-022 para detalle.

    Atributos:
        UNKNOWN: Código default cuando no hay una categoría específica.
    """

    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Error:
    """Error de operación (NO es una excepción).

    Representa qué salió mal en una operación que devolvió ``Failure``.

    Atributos:
        code: Código machine-readable (default: ``ErrorCode.UNKNOWN``).
        message: Mensaje legible para el desarrollador.
        detail: Información adicional opcional.

    No es una excepción. No hereda de ``Exception``.
    No tiene stack trace. No tiene lógica de logging.

    Uso::

        >>> err = Error(code=ErrorCode.UNKNOWN, message="Something went wrong")
        >>> str(err)
        '[UNKNOWN] Something went wrong'
    """

    code: ErrorCode = ErrorCode.UNKNOWN
    message: str = ""
    detail: str | None = None

    def __str__(self) -> str:
        """Retorna ``[CODE] message`` o ``[CODE] message: detail``."""
        if self.detail:
            return f"[{self.code.value}] {self.message}: {self.detail}"
        return f"[{self.code.value}] {self.message}"

    @classmethod
    def from_exception(cls, exception: Exception) -> Error:
        """
        Crea un ``Error`` desde una excepción ``FoundationError``.

        Preserva el código de la excepción como prefijo en el mensaje
        para no perder información semántica::

            err = Error.from_exception(DomainError("Topic already reviewed"))
            str(err)  # "[UNKNOWN] [DOMAIN_ERROR] Topic already reviewed"

        Si la excepción NO es ``FoundationError``, se usa ``str(exception)``
        como mensaje y ``ErrorCode.UNKNOWN`` como código.

        Args:
            exception: La excepción a envolver.

        Returns:
            Error con ``code=ErrorCode.UNKNOWN`` (por diferencia de tipos:
            ``FoundationError.code`` es ``ClassVar[str]``, ``Error.code`` es
            ``ErrorCode``). El mensaje preserva el código de excepción como
            prefijo ``"[EXCEPTION_CODE] message"``.
        """
        # Lazy import para evitar dependencia circular:
        # foundation.errors.base importa de foundation.result.result
        from foundation.errors.base import FoundationError as _FoundationError

        if isinstance(exception, _FoundationError):
            return cls(
                code=ErrorCode.UNKNOWN,
                message=f"[{exception.code}] {exception.message}".strip(),
                detail=exception.detail,
            )
        # Para excepciones que NO son FoundationError
        return cls(
            code=ErrorCode.UNKNOWN,
            message=str(exception),
        )


@dataclass(frozen=True)
class Result[T]:
    """Resultado de una operación que puede tener éxito o fallar.

    ``T`` es el tipo del valor en caso de éxito.

    Usar *factory methods* para construir::

        Result.success(value)  → Success[T]
        Result.failure(error)  → Failure[T]

    Inspección::

        result.is_success  → bool
        result.is_failure  → bool

    Acceso a datos (preferir pattern matching)::

        result.value  → T (raise si Failure)
        result.error  → Error (raise si Success)

    NO es una excepción. No sustituye excepciones para errores
    de programación o infraestructura.
    """

    @classmethod
    def success(cls, value: T) -> Result[T]:
        """Crea un resultado exitoso."""
        return Success(value=value)

    @classmethod
    def failure(cls, error: Error) -> Result[T]:
        """Crea un resultado fallido."""
        return Failure(error=error)

    @property
    def is_success(self) -> bool:
        """``True`` si el resultado es exitoso."""
        raise NotImplementedError

    @property
    def is_failure(self) -> bool:
        """``True`` si el resultado es fallido."""
        raise NotImplementedError

    def unwrap(self) -> T:
        """Retorna el valor o lanza ``RuntimeError`` si es ``Failure``.

        Returns:
            El valor de tipo ``T`` si es ``Success``.

        Raises:
            RuntimeError: Si el resultado es ``Failure``.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class Success[T](Result[T]):
    """Variante exitosa de ``Result[T]``.

    Contiene el valor de tipo ``T`` producido por la operación.
    """

    value: T

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False

    def unwrap(self) -> T:
        """Retorna el valor directamente."""
        return self.value

    @property
    def error(self) -> Error:
        raise RuntimeError("Cannot access error of a Success")


@dataclass(frozen=True)
class Failure[T](Result[T]):
    """Variante fallida de ``Result[T]``.

    Contiene el ``Error`` que describe qué salió mal.
    """

    error: Error

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True

    def unwrap(self) -> T:
        """Lanza ``RuntimeError`` porque ``Failure`` no tiene valor."""
        raise RuntimeError(f"Cannot unwrap Failure: {self.error}")

    @property
    def value(self) -> T:
        raise RuntimeError("Cannot access value of a Failure")
