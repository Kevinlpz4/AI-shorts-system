"""
Script Domain Exceptions
=========================
Errores de dominio para el módulo de Scripts.

Sigue la jerarquía definida en domain/exceptions/base.py.
Cada excepción hereda de ContentError (errores de contenido).

Jerarquía:
  DomainError
    └── ContentError
          ├── ScriptNotFoundError     (404)
          └── ScriptAlreadyExistsError (409)
"""

from .content import ContentError


class ScriptNotFoundError(ContentError):
    """
    El script solicitado no existe para el topic dado.

    HTTP: 404 Not Found
    """
    code: str = "SCRIPT_NOT_FOUND"
    status_code: int = 404
    message_template: str = "No se encontró un guion para el topic '{topic_id}'"


class ScriptAlreadyExistsError(ContentError):
    """
    Ya existe un script para este topic y no se pidió regeneración.

    HTTP: 409 Conflict
    """
    code: str = "SCRIPT_ALREADY_EXISTS"
    status_code: int = 409
    message_template: str = "Ya existe un guion para el topic '{topic_id}'. Usá regenerate para sobrescribirlo."
