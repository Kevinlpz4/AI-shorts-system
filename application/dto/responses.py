from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class ContentResult:
    """Resultado de generación de contenido."""
    success: bool
    message: str = ""
    data: Optional[Any] = None
    error_code: str = ""
    status_code: int = 200
    evaluations: list[dict] = field(default_factory=list)

    @classmethod
    def ok(cls, data: Any = None, message: str = "Operación exitosa") -> "ContentResult":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fallback(cls, data: Any = None, message: str = "Usando modo fallback") -> "ContentResult":
        return cls(success=True, message=message, data=data, status_code=200)

    @classmethod
    def error(cls, message: str, code: str = "ERROR", status: int = 500) -> "ContentResult":
        return cls(success=False, message=message, error_code=code, status_code=status)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error_code": self.error_code,
            "status_code": self.status_code,
        }


@dataclass
class EvaluationResponse:
    """Resultado de evaluación de contenido."""
    score: float
    classification: str
    criteria: dict
    recommendations: list[str]
    was_optimized: bool = False
    optimized_content: Optional[Any] = None
