from .base import DomainError


class TTSError(DomainError):
    code = "TTS_ERROR"
    status_code = 502
    log_level = "warning"
    message_template = "Error al generar el audio de voz"


class VideoRenderError(DomainError):
    code = "VIDEO_RENDER_ERROR"
    status_code = 500
    message_template = "Error al renderizar el video"


class SubtitlesError(DomainError):
    code = "SUBTITLES_ERROR"
    status_code = 500
    message_template = "Error al generar los subtítulos"
