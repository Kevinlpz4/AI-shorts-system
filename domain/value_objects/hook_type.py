from enum import Enum, auto


class HookType(Enum):
    """Tipos de hooks para contenido viral."""
    QUESTION = "question"          # Pregunta intrigante
    STATEMENT = "statement"        # Afirmación fuerte
    REVEAL = "reveal"              # Revelación/secreto
    LIST = "list"                  # Lista (5 cosas...)
    TRENDING = "trending"          # Referencia a trend
    CONTROVERSIAL = "controversial" # Afirmación controversial

    @classmethod
    def from_string(cls, value: str) -> "HookType":
        """Convierte string a HookType, default STATEMENT."""
        for member in cls:
            if member.value == value.lower():
                return member
        return cls.STATEMENT

    @property
    def base_score(self) -> int:
        """Score base de efectividad por tipo."""
        scores = {
            HookType.QUESTION: 90,
            HookType.REVEAL: 88,
            HookType.LIST: 85,
            HookType.TRENDING: 80,
            HookType.STATEMENT: 75,
            HookType.CONTROVERSIAL: 70,
        }
        return scores[self]

    @property
    def description(self) -> str:
        descs = {
            HookType.QUESTION: "Pregunta que genera curiosidad",
            HookType.STATEMENT: "Afirmación que capta atención",
            HookType.REVEAL: "Revelación que intriga",
            HookType.LIST: "Lista numerada predecible pero efectiva",
            HookType.TRENDING: "Referencia a lo que está en tendencia",
            HookType.CONTROVERSIAL: "Afirmación que genera debate",
        }
        return descs[self]
