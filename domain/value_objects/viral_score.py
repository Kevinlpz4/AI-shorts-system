from dataclasses import dataclass


@dataclass(frozen=True)
class ViralScore:
    """
    Value Object inmutable que representa el potencial viral (0-100).
    
    Comportamiento de dominio incluido:
    - Validación en creación
    - Comparación semántica
    - Operaciones de dominio (is_viral, combine)
    """
    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            raise ValueError(f"ViralScore debe estar entre 0 y 100, no {self.value}")

    def is_viral(self) -> bool:
        """Un score >= 80 se considera viral."""
        return self.value >= 80

    def is_promising(self) -> bool:
        """Un score >= 60 es prometedor."""
        return self.value >= 60

    def combine(self, other: "ViralScore") -> "ViralScore":
        """Combina dos scores (ej: trend score + idea score)."""
        return ViralScore(min(100, (self.value + other.value) // 2))

    def improve(self, amount: int = 10) -> "ViralScore":
        """Retorna un nuevo score mejorado."""
        return ViralScore(min(100, self.value + amount))

    def __str__(self) -> str:
        return f"{self.value}/100"

    def __int__(self) -> int:
        return self.value
