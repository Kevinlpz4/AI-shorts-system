import logging
from datetime import datetime
from typing import Optional

from domain.entities.video import VideoAsset
from domain.ports.publisher import PublishResult

logger = logging.getLogger(__name__)


class MockPublisher:
    """
    Publicador Mock para desarrollo/testing.
    
    Puerto que implementa: PublisherPort
    
    Simula la publicación sin llamar APIs reales.
    """
    
    def __init__(self, platform_name: str = "youtube"):
        self._platform = platform_name

    @property
    def platform(self) -> str:
        return self._platform

    async def publish(
        self,
        video: VideoAsset,
        title: str,
        description: str = "",
        tags: Optional[list[str]] = None,
    ) -> PublishResult:
        """Simula publicación."""
        logger.info(f"🚀 [MOCK] Publicando en {self._platform}: {title[:50]}...")

        fake_id = f"mock_{self._platform}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        return PublishResult(
            platform=self._platform,
            video_id=fake_id,
            url=f"https://{self._platform}.com/watch?v={fake_id}",
            status="published",
        )
