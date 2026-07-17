"""
ErrorMapper — convierte DomainError → Error con ``ApplicationErrorCode``.

Usa un diccionario de mapeo ``domain_code → ApplicationErrorCode`` para
evitar if/elif gigantes. Es fácilmente extensible: basta agregar una
entrada al diccionario.

Cubre todos los ``LearningErrorCode`` (dominio) y los ``ErrorCode``
de Foundation.

Uso::

    from foundation.errors import DomainError
    from learning.application.errors import ErrorMapper

    error = ErrorMapper.map_domain_error(domain_exception)
    # error.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
"""

from __future__ import annotations

from enum import Enum

from foundation.errors.base import DomainError
from foundation.result.result import Error as ResultError

from learning.application.exceptions.error_code import ApplicationErrorCode

# ── Mapeo de códigos de dominio → códigos de aplicación ──

_DOMAIN_TO_APPLICATION: dict[str, ApplicationErrorCode] = {
    # ── Feedback errors ──
    "FEEDBACK_NOT_FOUND": ApplicationErrorCode.RESOURCE_NOT_FOUND,
    "DUPLICATE_FEEDBACK": ApplicationErrorCode.COMMAND_INVALID,
    # ── Signal errors ──
    "SIGNAL_NOT_FOUND": ApplicationErrorCode.RESOURCE_NOT_FOUND,
    "SIGNAL_ALREADY_FINALIZED": ApplicationErrorCode.COMMAND_INVALID,
    # ── Source Quality errors ──
    "SOURCE_QUALITY_NOT_FOUND": ApplicationErrorCode.RESOURCE_NOT_FOUND,
    # ── Model errors ──
    "MODEL_NOT_FOUND": ApplicationErrorCode.RESOURCE_NOT_FOUND,
    # ── Validation errors ──
    "INVALID_DECISION_TYPE": ApplicationErrorCode.COMMAND_INVALID,
    "INVALID_CONFIDENCE": ApplicationErrorCode.COMMAND_INVALID,
    "INVALID_WEIGHTS": ApplicationErrorCode.COMMAND_INVALID,
    # ── Window errors ──
    "WINDOW_INVALID": ApplicationErrorCode.COMMAND_INVALID,
    # ── Data errors ──
    "INSUFFICIENT_DATA": ApplicationErrorCode.OPERATION_FAILED,
}


class ErrorMapper:
    """Convierte errores de dominio o Result en errores con ApplicationErrorCode.

    Sin lógica de if/elif: usa un diccionario de mapeo extensible.
    """

    @staticmethod
    def map_domain_error(error: DomainError) -> ResultError:
        """Convierte una excepción ``DomainError`` en un ``Error`` de Result.

        Busca ``error.code`` (ClassVar[str]) en el diccionario de mapeo.
        Si no encuentra el código, usa ``ApplicationErrorCode.OPERATION_FAILED``
        como fallback.

        Args:
            error: Excepción de dominio (DomainError o subclase).

        Returns:
            Error con ``ApplicationErrorCode`` mapeado.
        """
        app_code = _DOMAIN_TO_APPLICATION.get(
            error.code,  # type: ignore[arg-type]
            ApplicationErrorCode.OPERATION_FAILED,
        )
        return ResultError(
            code=app_code,  # type: ignore[arg-type]
            message=error.message,
            detail=error.detail,
        )

    @staticmethod
    def map_result_error(error: ResultError) -> ResultError:
        """Convierte un ``Error`` de Result (posiblemente con códigos de dominio)
        en un ``Error`` con ``ApplicationErrorCode``.

        Lee el ``.value`` del código si es un Enum, o lo convierte a string.
        Si el código NO está en el diccionario de mapeo, se retorna ``error``
        sin modificar (ya es un código de aplicación o desconocido).

        Args:
            error: Error de Result (Foundation).

        Returns:
            Error con ``ApplicationErrorCode`` mapeado, o el mismo error
            si el código ya es de aplicación o no está mapeado.
        """
        code_value = (
            error.code.value if isinstance(error.code, Enum) else str(error.code)
        )

        # Si ya es un ApplicationErrorCode, retornar sin cambios
        if isinstance(error.code, ApplicationErrorCode):
            return error

        # Buscar en el diccionario de mapeo
        app_code = _DOMAIN_TO_APPLICATION.get(
            code_value,
            ApplicationErrorCode.OPERATION_FAILED,
        )
        return ResultError(
            code=app_code,  # type: ignore[arg-type]
            message=error.message,
            detail=error.detail,
        )
