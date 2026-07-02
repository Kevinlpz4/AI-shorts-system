"""
Foundation Error Hierarchy — Excepciones base del sistema.

Arquitectura::

    FoundationError (Exception)
    ├── DomainError         — violación de regla de negocio
    ├── ApplicationError    — error de aplicación (comando inválido)
    └── InfrastructureError — error de infraestructura (DB caída, timeout)

Uso típico::

    # En un BC:
    class ResearchAlreadyReviewedError(DomainError):
        code = "RESEARCH_ALREADY_REVIEWED"

    # En un Application Service:
    try:
        result = await use_case.execute(cmd)
    except FoundationError as e:
        return Result.failure(e.to_error())

Principios:
    - ``FoundationError`` hereda de ``Exception`` (NO es frozen dataclass).
    - ``code`` es ``ClassVar[str]`` para evitar instanciación por error.
    - No mezclar con ``Error`` (dataclass frozen de Result) — son conceptos
      diferentes: ``FoundationError`` es para excepciones, ``Error`` es para
      flujos esperados via ``Result.failure()``.
    - ``to_error()`` preserva el código de excepción como prefijo en el mensaje
      para mantener trazabilidad semántica.

Ver también:
    :class:`foundation.result.result.Error`: Dataclass para Result Pattern.
    :class:`foundation.result.result.ErrorCode`: Enum de códigos Foundation.
"""

from __future__ import annotations

from typing import ClassVar

# Importado directamente: NO hay dependencia circular porque
# foundation.result.result NO importa de foundation.errors.base.
from foundation.result.result import Error as ResultError
from foundation.result.result import ErrorCode


class FoundationError(Exception):
    """
    Base de TODAS las excepciones del sistema.

    NO es un ``DomainError`` — es una base técnica.
    ``DomainError`` hereda de esta.

    Atributos:
        code: Código machine-readable (ClassVar — no se setea por instancia).
        message: Mensaje público legible (opcional, default ``""``).
        detail: Mensaje técnico para debugging (opcional, default ``""``).

    NO hace:
        - No es un ``Error`` de Result (no se usa en ``Result.failure()``
          directamente).
        - No tiene lógica de logging.
        - No tiene stack trace automático (usa el de ``Exception``).

    Uso::

        raise FoundationError("Something went wrong")
        raise FoundationError("Public message", detail="Debug info")
        raise FoundationError(detail="Debug without public message")
    """

    code: ClassVar[str] = "FOUNDATION_ERROR"

    def __init__(self, message: str = "", detail: str = "") -> None:
        self.message = message
        self.detail = detail
        super().__init__(self.detail)

    def to_dict(self) -> dict:
        """
        Serializa la excepción a diccionario.

        Útil para respuestas de API.
        """
        return {
            "error": self.code,
            "message": self.message,
            "detail": self.detail,
        }

    def to_error(self) -> ResultError:
        """
        Convierte esta excepción en un ``Error`` dataclass para Result.

        Preserva el código de excepción como prefijo en el mensaje::

            error = FoundationError("fail").to_error()
            str(error)  # "[FOUNDATION_ERROR] fail"

        Returns:
            Error con ``code=ErrorCode.UNKNOWN`` (por diferencia de tipos)
            y ``message`` con el código de excepción prefijado.
        """
        return ResultError(
            code=ErrorCode.UNKNOWN,
            message=f"[{self.code}] {self.message}".strip(),
            detail=self.detail,
        )


class DomainError(FoundationError):
    """Error de DOMINIO — violación de regla de negocio.

    Representa una situación donde una operación viola una regla
    del dominio (lenguaje ubicuo). Ejemplos:

    - ``ResearchAlreadyReviewedError``
    - ``CannotRemoveLastFeedError``
    - ``DuplicateTopicError``

    Atributos:
        code: Siempre ``"DOMAIN_ERROR"`` para esta clase.
    """
    code: ClassVar[str] = "DOMAIN_ERROR"


class ApplicationError(FoundationError):
    """Error de APLICACIÓN — comando inválido, operación no permitida.

    Representa errores de uso del sistema. NO son violaciones de
    reglas de negocio (eso va en ``DomainError``). Ejemplos:

    - ``CommandValidationError`` (payload inválido)
    - ``ResourceNotFoundError`` (en aplicación)
    - ``PermissionDeniedError``

    Atributos:
        code: Siempre ``"APPLICATION_ERROR"`` para esta clase.
    """
    code: ClassVar[str] = "APPLICATION_ERROR"


class InfrastructureError(FoundationError):
    """Error de INFRAESTRUCTURA — DB caída, timeout, red.

    Representa fallos técnicos que generalmente son irrecuperables
    en el momento y requieren degradación graceful. Ejemplos:

    - ``DatabaseConnectionError``
    - ``ExternalServiceTimeoutError``
    - ``SerializationError``

    Atributos:
        code: Siempre ``"INFRASTRUCTURE_ERROR"`` para esta clase.
    """
    code: ClassVar[str] = "INFRASTRUCTURE_ERROR"



