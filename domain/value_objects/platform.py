from enum import Enum


class Platform(Enum):
    """Plataformas destino para publicación."""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"

    @classmethod
    def from_string(cls, value: str) -> "Platform":
        for member in cls:
            if member.value == value.lower():
                return member
        raise ValueError(f"Plataforma no soportada: {value}")

    @property
    def aspect_ratio(self) -> str:
        ratios = {
            Platform.YOUTUBE: "9:16",
            Platform.TIKTOK: "9:16",
            Platform.INSTAGRAM: "9:16",
        }
        return ratios[self]

    @property
    def max_duration(self) -> int:
        """Duración máxima en segundos."""
        limits = {
            Platform.YOUTUBE: 60,
            Platform.TIKTOK: 180,
            Platform.INSTAGRAM: 90,
        }
        return limits[self]
