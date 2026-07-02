"""
EntityId — Value Object base para todos los IDs del sistema.

Responsabilidades:
  - Envolver un UUID con type safety
  - Garantizar que siempre es un UUID válido
  - Serialización a string y desde string
  - Igualdad por tipo concreto Y valor

Uso:
    # Crear un ID con UUID aleatorio
    eid = EntityId.new()

    # Crear con UUID específico
    eid = EntityId(value=UUID("..."))

    # Recuperar desde string
    eid = EntityId.from_string("...")

Ver Sprint 2.1 Spec para diseño completo y decisiones arquitectónicas.
"""

from dataclasses import dataclass, field
from typing import Self
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EntityId:
    """
    Value Object base para todos los IDs del sistema.

    Es un VO (no una Entity): no tiene identidad propia,
    igualdad por valor, inmutable.

    Responsabilidades:
      - Envolver un UUID con type safety
      - Garantizar que siempre es un UUID válido
      - Serialización a string y desde string
      - Igualdad por tipo concreto Y valor
      - Hash consistente con igualdad

    ¿Por qué frozen=True?
      - Un ID no cambia. Nunca. Si cambia, es otra entidad.

    ¿Por qué type(self) is type(other) en __eq__?
      - SourceId(x) NO debe ser igual a FeedId(x) aunque tengan el mismo UUID.
      - El type safety debe funcionar en runtime, no solo en type checker.
      - Ver Sprint 2.1 Spec, sección 7.2.
    """

    value: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        """Valida que value sea un UUID en tiempo de construcción.

        Fail Fast (F5): un objeto inválido no debe poder construirse.
        Python no enforcea type hints en runtime — esta validación
        asegura que value SIEMPRE sea un UUID.
        """
        if not isinstance(self.value, UUID):
            raise TypeError(
                f"value must be a uuid.UUID, got {type(self.value).__name__}"
            )

    def __str__(self) -> str:
        """Representación como string: solo el UUID, sin adornos."""
        return str(self.value)

    def __eq__(self, other: object) -> bool:
        """
        Igualdad por tipo concreto Y valor.

        Dos EntityId son iguales SOLO si:
          1. type(self) is type(other)  (mismo tipo concreto)
          2. self.value == other.value  (mismo UUID)

        IDs de diferentes tipos NUNCA son iguales, aunque tengan
        el mismo UUID.
        """
        if type(self) is not type(other):
            return NotImplemented
        # `other` es del mismo tipo que `self`, así que tiene `.value`
        return self.value == other.value  # type: ignore[union-attr]

    def __hash__(self) -> int:
        """Hash basado en el valor UUID."""
        return hash(self.value)

    @classmethod
    def from_string(cls, raw: str) -> Self:
        """
        Crea un ID desde string.

        Args:
            raw: String UUID en cualquier formato que UUID() acepte
                 (estándar, con llaves {}, sin guiones, con urn:).

        Returns:
            EntityId (o subclase) con el UUID especificado.

        Raises:
            ValueError: Si raw no es un UUID válido.
        """
        return cls(value=UUID(raw))

    @classmethod
    def new(cls) -> Self:
        """
        Crea un ID con nuevo UUID aleatorio.

        Es la forma PREFERIDA de crear IDs nuevos. Encapsula uuid4()
        para que el resto del sistema no dependa de la implementación.

        Returns:
            EntityId (o subclase) con UUID aleatorio único.
        """
        return cls()
