"""
Application Error Codes — ADR-022 compliant str, Enum.

Separado de ``LearningErrorCode`` (dominio) para mantener
clara la separación de responsabilidades:

- ``LearningErrorCode`` → errores de reglas de negocio del dominio
- ``ApplicationErrorCode`` → errores de la capa de aplicación

Uso::

    from learning.application.exceptions import ApplicationErrorCode

    error = Error(code=ApplicationErrorCode.COMMAND_INVALID, message="...")
"""

from __future__ import annotations

from enum import Enum


class ApplicationErrorCode(str, Enum):
    """Códigos de error para la capa de aplicación.

    Diferentes de LearningErrorCode (dominio). Representan
    problemas en el uso del sistema, no violaciones de reglas
    de negocio.

    Attributes:
        COMMAND_INVALID: Comando mal formado o con datos inválidos.
        COMMAND_MISSING_FIELD: Campo requerido ausente en el comando.
        RESOURCE_NOT_FOUND: Recurso solicitado no encontrado.
        OPERATION_FAILED: Operación fallida por error interno.
        TRANSACTION_FAILED: La transacción no pudo completarse.
        CONCURRENCY_CONFLICT: Conflicto de concurrencia (optimistic lock).
    """

    COMMAND_INVALID = "COMMAND_INVALID"
    COMMAND_MISSING_FIELD = "COMMAND_MISSING_FIELD"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    OPERATION_FAILED = "OPERATION_FAILED"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"
    CONCURRENCY_CONFLICT = "CONCURRENCY_CONFLICT"
