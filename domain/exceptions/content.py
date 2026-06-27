from .base import DomainError


class ContentError(DomainError):
    """Base para errores de contenido."""
    code = "CONTENT_ERROR"
    status_code = 422


class IdeaGenerationError(ContentError):
    code = "IDEA_GENERATION_ERROR"
    message_template = "No se pudo generar la idea de contenido"


class ScriptGenerationError(ContentError):
    code = "SCRIPT_GENERATION_ERROR"
    message_template = "No se pudo generar el guion"


class ScriptValidationError(ContentError):
    code = "SCRIPT_VALIDATION_ERROR"
    message_template = "El guion no pasa la validación de calidad"


class HookGenerationError(ContentError):
    code = "HOOK_GENERATION_ERROR"
    message_template = "No se pudieron generar los hooks"


class ContentEvaluationError(ContentError):
    code = "CONTENT_EVALUATION_ERROR"
    message_template = "Error al evaluar la calidad del contenido"
