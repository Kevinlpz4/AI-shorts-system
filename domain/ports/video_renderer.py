from typing import Protocol, Optional

from domain.entities.video import VideoAsset
from domain.entities.script import Script


class VideoRenderer(Protocol):
    """
    Puerto: Renderizador de videos.
    
    Implementaciones: MoviePy, FFmpeg, Mock.
    """
    
    async def render(
        self,
        audio_path: str,
        script: Script,
        aspect_ratio: str = "9:16",
        template: str = "default",
    ) -> VideoAsset:
        """Renderiza un video a partir de audio + guion."""
        ...

    @property
    def available(self) -> bool:
        ...
