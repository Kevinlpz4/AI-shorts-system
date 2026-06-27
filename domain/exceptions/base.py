class DomainError(Exception):
    """
    Base de TODOS los errores de dominio.
    
    Cada subclase define:
    - code: Código machine-readable
    - status_code: HTTP status code
    - log_level: Nivel de logging
    - message_template: Mensaje para el usuario
    """
    code: str = "DOMAIN_ERROR"
    status_code: int = 500
    log_level: str = "error"
    message_template: str = "Error inesperado en el sistema"

    def __init__(self, detail: str = "", **kwargs):
        if detail:
            self.detail = detail.format(**kwargs) if kwargs else detail
        elif kwargs:
            self.detail = self.message_template.format(**kwargs)
        else:
            self.detail = detail
        super().__init__(self.detail or self.message_template)

    @property
    def user_message(self) -> str:
        return self.detail or self.message_template

    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.user_message,
            "detail": self.detail,
            "status_code": self.status_code,
        }
