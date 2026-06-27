from .base import DomainError


class TrendNotFoundError(DomainError):
    code = "TREND_NOT_FOUND"
    status_code = 404
    log_level = "info"
    message_template = "No se encontraron tendencias para este nicho"


class TrendSourceError(DomainError):
    code = "TREND_SOURCE_ERROR"
    status_code = 502
    log_level = "warning"
    message_template = "Error al obtener tendencias de fuente externa"
