from .base import DomainError


class PublishError(DomainError):
    code = "PUBLISH_ERROR"
    status_code = 502
    log_level = "error"
    message_template = "Error al publicar el video"


class PlatformNotSupportedError(PublishError):
    code = "PLATFORM_NOT_SUPPORTED"
    status_code = 400
    message_template = "La plataforma '{platform}' no está soportada"


class UploadFailedError(PublishError):
    code = "UPLOAD_FAILED"
    message_template = "Error al subir el video a la plataforma"
