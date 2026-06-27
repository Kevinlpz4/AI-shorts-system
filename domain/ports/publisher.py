from typing import Protocol, Optional

from domain.entities.video import VideoAsset
from domain.value_objects.platform import Platform


class PublishResult:
    """Resultado de una publicación."""
    def __init__(
        self,
        platform: str,
        video_id: str = "",
        url: str = "",
        status: str = "pending",
        error: Optional[str] = None,
    ):
        self.platform = platform
        self.video_id = video_id
        self.url = url
        self.status = status
        self.error = error

    @property
    def is_success(self) -> bool:
        return self.status in ("success", "uploaded", "published")

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "video_id": self.video_id,
            "url": self.url,
            "status": self.status,
            "error": self.error,
        }


class PublisherPort(Protocol):
    """
    Puerto: Publicador de videos en plataformas.
    
    Implementaciones: YouTube, TikTok, Instagram, Mock.
    """
    
    async def publish(
        self,
        video: VideoAsset,
        title: str,
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> PublishResult:
        """Publica un video en la plataforma."""
        ...

    @property
    def platform(self) -> str:
        """Nombre de la plataforma."""
        ...
