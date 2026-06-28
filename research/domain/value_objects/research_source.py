"""
ResearchSource — Origen de un ResearchTopic
=============================================
Value Object inmutable que describe de DÓNDE vino la información.

Tipos de fuente:
  - MANUAL: el usuario proveyó el contenido directamente (texto, enlace, tema)
  - AUTOMATIC: se obtuvo de una fuente externa (Google News, Twitter, etc.)

Cada fuente tiene un nivel de confiabilidad (0-100) que influye
en el ResearchScore final.

Ejemplos:
  ResearchSource(name="manual", type=SourceType.MANUAL, reliability=100)
  ResearchSource(name="google-news", type=SourceType.AUTOMATIC, reliability=80)
  ResearchSource(name="twitter", type=SourceType.AUTOMATIC, reliability=50)
"""

from dataclasses import dataclass
from enum import Enum


class SourceType(Enum):
    """Clasificación del tipo de fuente."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"


@dataclass(frozen=True)
class ResearchSource:
    """
    Value Object: origen de la investigación.

    Frozen = inmutable. Una vez creado, no cambia.
    Sin identidad → dos ResearchSource con mismos atributos son iguales.
    """

    name: str
    type: SourceType
    reliability: int = 50  # 0-100, default neutral

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("ResearchSource.name no puede estar vacío")
        if not 0 <= self.reliability <= 100:
            raise ValueError(
                f"ResearchSource.reliability debe estar entre 0-100, no {self.reliability}"
            )

    @classmethod
    def manual(cls, name: str = "manual") -> "ResearchSource":
        """Fuente manual: el usuario ingresó los datos directamente."""
        return cls(name=name, type=SourceType.MANUAL, reliability=100)

    @classmethod
    def google_news(cls) -> "ResearchSource":
        return cls(name="google-news", type=SourceType.AUTOMATIC, reliability=80)

    @classmethod
    def twitter(cls) -> "ResearchSource":
        return cls(name="twitter", type=SourceType.AUTOMATIC, reliability=50)
