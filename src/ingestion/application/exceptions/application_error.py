"""
Application Error Hierarchy — errores de la capa de aplicación.

Jerarquía::

    foundation.errors.ApplicationError
    ├── CommandValidationError    ← comando inválido o mal formado
    └── ResourceNotFoundError     ← recurso no encontrado

NO incluye:
    - IngestionError (dominio) — violaciones de reglas de negocio
    - InfrastructureError — fallos técnicos (DB, red)

Uso::

    from ingestion.application.exceptions import CommandValidationError

    raise CommandValidationError("Field 'source_id' is required")
"""

from __future__ import annotations

from foundation.errors.base import ApplicationError


class CommandValidationError(ApplicationError):
    """Comando inválido — payload mal formado o datos incorrectos.

    Se utiliza cuando un Command o Query no pasa validación
    básica de estructura (campos faltantes, tipos incorrectos).

    Attributes:
        code: Siempre ``"COMMAND_VALIDATION_ERROR"``.
    """

    code: str = "COMMAND_VALIDATION_ERROR"


class ResourceNotFoundError(ApplicationError):
    """Recurso no encontrado en la capa de aplicación.

    Diferente de los errores de repositorio del dominio:
    este error se usa cuando la aplicación busca un recurso
    que debería existir pero no está disponible.

    Attributes:
        code: Siempre ``"RESOURCE_NOT_FOUND_ERROR"``.
    """

    code: str = "RESOURCE_NOT_FOUND_ERROR"
