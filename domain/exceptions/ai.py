from .base import DomainError


class AIProviderError(DomainError):
    """Base para errores de proveedores de IA."""
    code = "AI_PROVIDER_ERROR"
    status_code = 503


class QuotaExceededError(AIProviderError):
    code = "QUOTA_EXCEEDED"
    status_code = 429
    log_level = "warning"
    message_template = "El proveedor de IA no tiene créditos disponibles"


class ProviderUnavailableError(AIProviderError):
    code = "PROVIDER_UNAVAILABLE"
    status_code = 503
    log_level = "warning"
    message_template = "El proveedor de IA está temporalmente fuera de servicio"


class RateLimitError(AIProviderError):
    code = "RATE_LIMIT_EXCEEDED"
    status_code = 429
    log_level = "warning"
    message_template = "Límite de tasa excedido para el proveedor de IA"


class InvalidProviderConfigError(AIProviderError):
    code = "INVALID_PROVIDER_CONFIG"
    status_code = 500
    message_template = "Configuración inválida del proveedor de IA"
