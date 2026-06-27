from dataclasses import dataclass


@dataclass(frozen=True)
class Duration:
    """
    Value Object inmutable para duración de contenido (segundos).
    
    Rules:
    - Shorts óptimos: 30-60 segundos
    - Máximo recomendado: 90 segundos
    - Hook: 3-5 segundos
    - CTA: 5 segundos
    """
    seconds: int

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError(f"Duration debe ser positiva, no {self.seconds}")
        if self.seconds > 600:
            raise ValueError(f"Duration máxima 600s, no {self.seconds}")

    @property
    def hook_duration(self) -> int:
        return min(5, max(3, int(self.seconds * 0.1)))

    @property
    def cta_duration(self) -> int:
        return min(5, int(self.seconds * 0.1))

    @property
    def body_duration(self) -> int:
        return self.seconds - self.hook_duration - self.cta_duration

    def is_optimal_for_shorts(self) -> bool:
        return 30 <= self.seconds <= 60

    def estimated_words(self) -> int:
        """~150 palabras por minuto = 2.5 palabras/segundo."""
        return int(self.seconds * 2.5)

    def __int__(self) -> int:
        return self.seconds

    def __str__(self) -> str:
        if self.seconds < 60:
            return f"{self.seconds}s"
        return f"{self.seconds // 60}m{self.seconds % 60}s"
