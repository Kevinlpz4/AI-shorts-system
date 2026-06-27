"""
Error Mapper — DomainError → respuesta amigable
==================================================
Mapea cualquier DomainError a:
- log_level para logging
- user_message para el usuario
- http_status para APIs HTTP
"""
import logging
from domain.exceptions.base import DomainError
from domain.exceptions.ai import QuotaExceededError, ProviderUnavailableError, RateLimitError
from domain.exceptions.content import (
    IdeaGenerationError, ScriptGenerationError, ScriptValidationError,
    ContentEvaluationError,
)
from domain.exceptions.trends import TrendNotFoundError
from domain.exceptions.media import TTSError, VideoRenderError
from domain.exceptions.publishing import PublishError, PlatformNotSupportedError


class ErrorMapper:
    """
    Mapea DomainError → (log_level, user_message, http_status).
    
    La aplicación usa esto para decidir QUÉ hacer con cada error.
    """

    _MAPPING: dict[type[DomainError], tuple[int, str]] = {
        # AI Provider Errors
        QuotaExceededError:       (logging.WARNING, "Proveedor de IA sin créditos, usando respaldo"),
        ProviderUnavailableError: (logging.WARNING, "Proveedor de IA temporalmente caído"),
        RateLimitError:           (logging.WARNING, "Límite de requests excedido, reintentando"),
        # Content Errors
        IdeaGenerationError:      (logging.ERROR, "No se pudo generar la idea"),
        ScriptGenerationError:    (logging.ERROR, "No se pudo generar el guion"),
        ScriptValidationError:    (logging.ERROR, "El guion no pasa control de calidad"),
        ContentEvaluationError:   (logging.ERROR, "Error evaluando contenido"),
        # Trend Errors
        TrendNotFoundError:       (logging.INFO, "No hay tendencias para este nicho"),
        # Media Errors
        TTSError:                 (logging.WARNING, "Error generando audio, usando voz sintética"),
        VideoRenderError:         (logging.ERROR, "Error renderizando video"),
        # Publishing Errors
        PublishError:             (logging.ERROR, "Error publicando video"),
        PlatformNotSupportedError:(logging.ERROR, "Plataforma no soportada"),
    }

    @classmethod
    def map(cls, error: DomainError) -> tuple[int, str, int]:
        """
        Mapea un DomainError.
        
        Returns:
            Tuple (log_level, user_message, http_status_code)
        """
        log_level, message = cls._MAPPING.get(
            type(error),
            (logging.ERROR, "Error inesperado en el sistema"),
        )
        return log_level, message, error.status_code

    @classmethod
    def to_response(cls, error: DomainError) -> dict:
        """Para respuestas API HTTP."""
        log_level, message, status = cls.map(error)
        return {
            "error": error.code,
            "message": message,
            "detail": error.detail,
            "status_code": status,
            "level": logging.getLevelName(log_level),
        }

    @classmethod
    def should_retry(cls, error: DomainError) -> bool:
        """Indica si se debería reintentar la operación."""
        return isinstance(error, (RateLimitError, ProviderUnavailableError))

    @classmethod
    def should_fallback(cls, error: DomainError) -> bool:
        """Indica si se debería usar fallback."""
        return isinstance(error, (QuotaExceededError, ProviderUnavailableError, TTSError))
