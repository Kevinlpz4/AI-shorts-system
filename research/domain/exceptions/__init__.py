"""
Research Domain Exceptions
==========================
Jerarquía de errores del módulo Research.

Sigue el mismo patrón que domain/exceptions/base.py (DomainError).
Cada excepción tiene:
  - code: identificador machine-readable
  - message_template: mensaje para el usuario
  - status_code: HTTP status code (para cuando haya API)
"""

from domain.exceptions.base import DomainError


class ResearchError(DomainError):
    """Base de TODOS los errores del módulo Research."""
    code: str = "RESEARCH_ERROR"
    status_code: int = 500


class SourceNotAvailableError(ResearchError):
    """
    Una fuente de investigación no está disponible temporalmente.
    Ej: Google News rate-limited, Twitter API down.
    """
    code: str = "SOURCE_NOT_AVAILABLE"
    status_code: int = 503
    message_template: str = "La fuente '{source_name}' no está disponible"


class NoResultsFoundError(ResearchError):
    """
    No se encontraron resultados para la consulta.
    No es necesariamente un error — puede ser que no haya noticias
    sobre el tema solicitado.
    """
    code: str = "NO_RESULTS_FOUND"
    status_code: int = 404
    message_template: str = "No se encontraron resultados para '{query}'"


class InvalidManualInputError(ResearchError):
    """
    El input manual del usuario no es válido.
    Ej: enlace mal formado, texto vacío, tema sin sentido.
    """
    code: str = "INVALID_MANUAL_INPUT"
    status_code: int = 400
    message_template: str = "El input proporcionado no es válido: {reason}"


class ResearchAlreadyReviewedError(ResearchError):
    """
    Se intentó aprobar/rechazar un topic que ya fue revisado.
    Solo los topics en PENDING_REVIEW pueden ser aprobados o rechazados.
    """
    code: str = "ALREADY_REVIEWED"
    status_code: int = 409
    message_template: str = "El topic ya fue {status}, no se puede modificar"


class ResearchTopicNotFoundError(ResearchError):
    """El topic solicitado no existe."""
    code: str = "RESEARCH_TOPIC_NOT_FOUND"
    status_code: int = 404
    message_template: str = "Topic no encontrado: {topic_id}"


class DuplicateDetectionError(ResearchError):
    """Error durante la detección de duplicados."""
    code: str = "DUPLICATE_DETECTION_ERROR"
    status_code: int = 500
